use std::path::Path;
use std::process::Command;
fn git_stdout(args: &[&str]) -> Option<String> {
    Command::new("git")
        .args(args)
        .output()
        .ok()
        .filter(|o| o.status.success())
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
}
fn main() {
    println!("cargo:rerun-if-env-changed=GROK_VERSION");
    println!("cargo:rerun-if-env-changed=KITE_BUILD_COMMIT");
    let mut watch_paths = Vec::new();
    watch_paths.extend(git_stdout(&["rev-parse", "--git-path", "HEAD"]));
    watch_paths.extend(git_stdout(&["rev-parse", "--git-path", "logs/HEAD"]));
    if let Some(head_ref) = git_stdout(&["symbolic-ref", "-q", "HEAD"]) {
        watch_paths.extend(git_stdout(&["rev-parse", "--git-path", &head_ref]));
    }
    for path in watch_paths.iter().filter(|p| Path::new(p).exists()) {
        println!("cargo:rerun-if-changed={path}");
    }
    // Remote release builds upload source without .git. The build driver passes
    // the source revision explicitly; local builds can still read it from Git.
    let commit = std::env::var("KITE_BUILD_COMMIT")
        .ok()
        .or_else(|| git_stdout(&["rev-parse", "HEAD"]))
        .map(|revision| {
            let hash = revision.strip_suffix("-dirty").unwrap_or(&revision);
            assert!(
                hash.len() >= 12 && hash.bytes().all(|byte| byte.is_ascii_hexdigit()),
                "KITE_BUILD_COMMIT must be a Git revision, optionally followed by -dirty"
            );
            let short: String = hash.chars().take(12).collect();
            if revision.ends_with("-dirty") {
                format!("{short}-dirty")
            } else {
                short
            }
        })
        .unwrap_or_else(|| "unknown".to_string());
    let version = std::env::var("GROK_VERSION")
        .or_else(|_| std::env::var("CARGO_PKG_VERSION"))
        .unwrap_or_else(|_| "0.0.0".to_string());
    println!("cargo:rustc-env=VERSION_WITH_COMMIT={version} ({commit})");
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows")
        && std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc")
    {
        println!("cargo:rustc-link-arg=/DELAYLOAD:ProjectedFSLib.dll");
        println!("cargo:rustc-link-arg=delayimp.lib");
    }
}
