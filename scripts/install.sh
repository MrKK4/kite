#!/usr/bin/env bash
# Git Bash installer. Windows releases currently provide the only native binary.
set -euo pipefail

case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) ;;
    *)
        echo 'Kite currently publishes Windows x64 binaries. Use PowerShell or Git Bash on Windows.' >&2
        echo 'Native Linux/macOS release binaries are not available yet; see the README for source builds.' >&2
        exit 1
        ;;
esac

for dependency in curl cygpath powershell.exe; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing $dependency. Run this installer from Git Bash on Windows." >&2
        exit 1
    fi
done

temporary_directory="$(mktemp -d)"
trap 'rm -f -- "$temporary_directory/install.ps1"; rmdir -- "$temporary_directory"' EXIT
curl -fsSL --retry 3 \
    https://raw.githubusercontent.com/MrKK4/kite/main/scripts/install.ps1 \
    -o "$temporary_directory/install.ps1"

install_directory="${KITE_INSTALL_DIR:-$HOME/.kite/bin}"
export KITE_INSTALL_DIR="$(cygpath -aw "$install_directory")"
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass \
    -File "$(cygpath -aw "$temporary_directory/install.ps1")"

# A child process cannot update the parent Git Bash session's PATH.
install_directory="$(cygpath -au "$KITE_INSTALL_DIR")"
case ":$PATH:" in
    *":$install_directory:"*) ;;
    *)
        echo
        echo 'Restart Git Bash, or run this command in the current terminal:'
        printf 'export PATH=%q:"$PATH"\n' "$install_directory"
        ;;
esac
