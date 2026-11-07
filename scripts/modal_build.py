"""Build Kite on Modal CPUs: modal run scripts/modal_build.py --target windows.

Only source is uploaded. Rust compilation runs remotely with 16 CPUs and 64 GiB
RAM. Downloads are cached; compilation uses fast container-local disk.
"""

from pathlib import Path
import hashlib
import os
import subprocess
import tempfile

import modal

ROOT = Path(__file__).resolve().parents[1]
app = modal.App("kite-build")
cache = modal.Volume.from_name("kite-build-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install(
        "build-essential", "curl", "git", "pkg-config", "cmake", "ninja-build",
        "clang", "lld", "llvm", "libclang-dev", "protobuf-compiler", "libssl-dev",
        "nasm", "ripgrep", "libxcb1-dev", "libxkbcommon-dev", "libdbus-1-dev",
    )
    .env({
        "RUSTUP_HOME": "/opt/rustup",
        "CARGO_HOME": "/opt/cargo",
        "PATH": "/opt/cargo/bin:/usr/local/bin:/usr/bin:/bin",
    })
    .run_commands(
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup-init.sh",
        "sh /tmp/rustup-init.sh -y --profile minimal --default-toolchain 1.94.0 --component rustfmt,clippy --target x86_64-pc-windows-msvc",
    )
    .pip_install("cargo-xwin")
    .add_local_dir(
        ROOT, "/src",
        ignore=[".git/**", "target/**", "dist/**", "**/__pycache__/**", "*.log", ".env", ".env.*"],
    )
)


@app.function(image=image, cpu=16, memory=65536, timeout=14400, volumes={"/cache": cache})
def build(target: str = "windows", mode: str = "build") -> dict:
    import shutil

    shutil.copytree("/src", "/work/kite", dirs_exist_ok=True)
    os.chdir("/work/kite")
    os.environ.update({
        # Cargo's SQLite bookkeeping must stay on the container filesystem;
        # byte-range locks can stall on a shared Modal Volume.
        "CARGO_HOME": "/work/cargo",
        "CARGO_TARGET_DIR": "/work/target",
        "CARGO_INCREMENTAL": "0",
        "CARGO_BUILD_JOBS": "16",
        "CARGO_PROFILE_DEV_DEBUG": "0",
        "CARGO_PROFILE_TEST_DEBUG": "0",
        "XWIN_CACHE_DIR": "/cache/xwin",
        "XWIN_ACCEPT_LICENSE": "1",
        "PROTOC": "/usr/bin/protoc",
        "KITE_HOME": "/tmp/kite-build-home",
    })
    # Keep registry downloads reusable without sharing Cargo's SQLite database
    # or lock files between containers. Only one build uses this Volume at a time.
    cargo_home = Path("/work/cargo")
    cargo_home.mkdir(parents=True, exist_ok=True)
    for directory in ("registry", "git"):
        saved = Path("/cache/cargo") / directory
        saved.mkdir(parents=True, exist_ok=True)
        (cargo_home / directory).symlink_to(saved, target_is_directory=True)

    def run(args: list[str]) -> None:
        print("+", " ".join(args), flush=True)
        subprocess.run(args, check=True)

    def format_source() -> str:
        files = Path("scripts/format-files.txt").read_text().splitlines()
        run(["rustfmt", "--edition", "2024", "--config", "skip_children=true", *files])
        import zipfile
        with zipfile.ZipFile("/cache/formatted.zip", "w", zipfile.ZIP_DEFLATED, strict_timestamps=False) as output:
            for file in files:
                output.write(file, file)
        return "formatted.zip"

    try:
        if mode == "lock":
            # Minimal lock refresh after dependency edits: only workspace entries change.
            run(["cargo", "update", "--workspace"])
            shutil.copy2("Cargo.lock", "/cache/Cargo.lock")
            return {"artifact": "Cargo.lock"}
        if mode == "test":
            # Every crate Kite modifies; --no-fail-fast so one failure doesn't hide the rest.
            run(["python3", "crates/codegen/kite-agent/scripts/encrypt_templates.py"])
            crates = [
                "kite-dirs", "kite-config-types", "kite-config", "kite-markdown",
                "kite-tools", "kite-agent", "kite-hooks", "kite-workspace",
                "kite-pager-render", "kite-pager", "kite-shell", "kite-sampler",
            ]
            # Debug test threads overflow the default stack (aborting kite-shell, even
            # upstream); tests that point GROK_HOME at a temp dir must not see KITE_HOME.
            test_env = {k: v for k, v in os.environ.items() if k != "KITE_HOME"}
            test_env["RUST_MIN_STACK"] = str(16 * 1024 * 1024)
            # One crate at a time with a time limit, so a hanging test cannot eat the whole run;
            # the log is saved after each crate.
            log, ok, timed_out = "", True, []
            for crate in crates:
                args = ["timeout", "1500", "cargo", "test", "--locked", "--lib", "--no-fail-fast", "-p", crate]
                print("+", " ".join(args), flush=True)
                result = subprocess.run(args, capture_output=True, text=True, env=test_env)
                if result.returncode == 124:
                    timed_out.append(crate)
                ok = ok and result.returncode == 0
                log += f"\n===== {crate} (exit {result.returncode}) =====\n" + result.stdout + result.stderr
                Path("/cache/test.log").write_text(log)
                cache.commit()
            failed = sorted({line.split()[1] for line in log.splitlines()
                             if line.startswith("test ") and line.endswith("FAILED")})
            return {"tests": "passed" if ok else "failed", "timed_out": timed_out,
                    "failed": failed, "artifact": "test.log"}
        if mode == "fmt":
            return {"artifact": format_source()}
        # The system prompt ships as an XOR-obfuscated copy of templates/*.md; a
        # template edit without regenerating silently builds the old prompt.
        run(["python3", "crates/codegen/kite-agent/scripts/encrypt_templates.py"])
        formatted = format_source()
        if target == "windows":
            run(["cargo", "xwin", "build", "--locked", "--release", "--target", "x86_64-pc-windows-msvc", "-p", "kite-pager-bin", "--bin", "kite"])
            artifact = Path("/work/target/x86_64-pc-windows-msvc/release/kite.exe")
        elif target == "linux":
            run(["cargo", "build", "--locked", "--release", "-p", "kite-pager-bin", "--bin", "kite"])
            artifact = Path("/work/target/release/kite")
            run([str(artifact), "--version"])
        else:
            raise ValueError("target must be windows or linux")
        shutil.copy2(artifact, Path("/cache") / artifact.name)
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        return {"artifact": artifact.name, "formatted": formatted, "sha256": digest}
    finally:
        cache.commit()


@app.local_entrypoint()
def main(target: str = "windows", mode: str = "build"):
    result = build.remote(target, mode)
    print(result)
    for name in (result.get("artifact"), result.get("formatted")):
        if not name:
            continue
        destination = ROOT / "dist" / name
        destination.parent.mkdir(exist_ok=True)
        # Windows cannot replace a running executable. Download completely before
        # touching the installed copy, then keep a uniquely named build if locked.
        with tempfile.NamedTemporaryFile(
            dir=destination.parent, prefix=f".{name}.", suffix=".download", delete=False,
        ) as output:
            pending = Path(output.name)
            try:
                for chunk in cache.read_file(name):
                    output.write(chunk)
            except BaseException:
                output.close()
                pending.unlink(missing_ok=True)
                raise
        try:
            try:
                pending.replace(destination)
            except PermissionError:
                digest = hashlib.sha256(pending.read_bytes()).hexdigest()[:12]
                destination = destination.with_stem(f"{destination.stem}-{digest}")
                pending.replace(destination)
                print("Existing artifact is locked; saved the new build separately.")
        finally:
            pending.unlink(missing_ok=True)
        print(f"Downloaded {destination}")
