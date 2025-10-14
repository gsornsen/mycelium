#!/bin/bash
# Mycelium Dependency Checker
# Version: 1.0
# Pre-flight check for all dependencies

echo "Checking Mycelium dependencies..."
echo ""

errors=0
warnings=0

# Required: Python 3
echo "Required Dependencies:"
echo "--------------------"

if command -v python3 &>/dev/null; then
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    python_major=$(echo "$python_version" | cut -d'.' -f1)
    python_minor=$(echo "$python_version" | cut -d'.' -f2)

    if [ "$python_major" -ge 3 ] && [ "$python_minor" -ge 10 ]; then
        echo "  python3: $python_version"
    else
        echo "  python3: $python_version (ERROR: requires 3.10+)"
        errors=$((errors + 1))
    fi
else
    echo "  python3: not found (REQUIRED)"
    echo "    Install from: https://www.python.org/downloads/"
    errors=$((errors + 1))
fi

# Required: Git
if command -v git &>/dev/null; then
    git_version=$(git --version 2>&1 | cut -d' ' -f3)
    echo "  git: $git_version"
else
    echo "  git: not found (REQUIRED)"
    echo "    Install:"
    echo "      Ubuntu/Debian: sudo apt-get install git"
    echo "      macOS: brew install git"
    echo "      Fedora: sudo dnf install git"
    errors=$((errors + 1))
fi

echo ""
echo "Optional Dependencies:"
echo "---------------------"

# Optional but recommended: uv
if command -v uv &>/dev/null; then
    uv_version=$(uv --version 2>&1)
    echo "  uv: $uv_version"
else
    echo "  uv: not found (recommended for fast venv management)"
    echo "    Install from: https://github.com/astral-sh/uv"
    echo "      curl -LsSf https://astral.sh/uv/install.sh | sh"
    warnings=$((warnings + 1))
fi

# Optional: direnv
if command -v direnv &>/dev/null; then
    direnv_version=$(direnv version 2>&1)

    # Check version (need 2.28.0+ for PATH_add)
    if echo "$direnv_version" | grep -qE "2\.(2[8-9]|[3-9][0-9])"; then
        echo "  direnv: $direnv_version"
    else
        echo "  direnv: $direnv_version (WARNING: 2.28.0+ recommended)"
        warnings=$((warnings + 1))
    fi

    # Check if hook is configured
    shell=$(basename "$SHELL")
    hook_configured=0

    case "$shell" in
        bash)
            if [ -f "$HOME/.bashrc" ] && grep -q 'direnv hook bash' "$HOME/.bashrc"; then
                hook_configured=1
            fi
            ;;
        zsh)
            if [ -f "$HOME/.zshrc" ] && grep -q 'direnv hook zsh' "$HOME/.zshrc"; then
                hook_configured=1
            fi
            ;;
    esac

    if [ $hook_configured -eq 0 ]; then
        echo "    Note: direnv hook not configured in shell RC file"
        echo "    Add to ~/${shell}rc:"
        echo "      eval \"\$(direnv hook $shell)\""
    fi
else
    echo "  direnv: not found (optional, enables automatic activation)"
    echo "    Install from: https://direnv.net/docs/installation.html"
    echo "    Without direnv, use manual activation: source bin/activate.sh"
    warnings=$((warnings + 1))
fi

# Optional: make (for development tasks)
if command -v make &>/dev/null; then
    make_version=$(make --version 2>&1 | head -n1)
    echo "  make: $make_version"
else
    echo "  make: not found (optional, for development tasks)"
fi

echo ""
echo "System Information:"
echo "------------------"

# Check disk space
if command -v df &>/dev/null; then
    home_free=$(df -h "$HOME" 2>/dev/null | tail -1 | awk '{print $4}')
    echo "  Free space in HOME: $home_free"

    # Parse size and warn if < 1GB
    free_gb=$(df -BG "$HOME" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$free_gb" -lt 1 ]; then
        echo "    WARNING: Low disk space (< 1GB free)"
        warnings=$((warnings + 1))
    fi
fi

# Check write permissions
echo "  Write permissions:"
for dir in "$HOME/.config" "$HOME/.local" "$HOME/.cache"; do
    if [ -d "$dir" ]; then
        if [ -w "$dir" ]; then
            echo "    $dir:"
        else
            echo "    $dir: NO (REQUIRED)"
            errors=$((errors + 1))
        fi
    else
        echo "    $dir: will be created"
    fi
done

# WSL detection
if [ -f /proc/version ] && grep -qi microsoft /proc/version 2>/dev/null; then
    echo "  Platform: WSL2"
    if [[ "$(pwd)" == /mnt/* ]]; then
        echo "    WARNING: Currently in Windows filesystem (/mnt/c/)"
        echo "             Consider cloning to WSL filesystem for better performance"
        warnings=$((warnings + 1))
    fi
fi

# Check for conflicting environment variables
echo ""
echo "Environment Check:"
echo "-----------------"
conflicts=$(env | grep "^MYCELIUM_" | grep -v "^MYCELIUM_ENV_ACTIVE=" || true)
if [ -n "$conflicts" ] && [ -z "$MYCELIUM_ENV_ACTIVE" ]; then
    echo "  WARNING: Found conflicting MYCELIUM_* variables (not from activation):"
    echo "$conflicts" | sed 's/^/    /'
    echo "  These may cause issues. Consider unsetting them."
    warnings=$((warnings + 1))
else
    echo "  No conflicting environment variables"
fi

# Summary
echo ""
echo "=== Summary ==="
echo ""

if [ $errors -gt 0 ]; then
    echo "FAILED: $errors required dependencies missing"
    echo ""
    echo "Fix the errors above and run this script again."
    exit 1
elif [ $warnings -gt 0 ]; then
    echo "PASSED with warnings: $warnings optional dependencies missing"
    echo ""
    echo "You can proceed, but installing optional dependencies is recommended."
    echo ""
    echo "Next steps:"
    echo "  1. Install uv (if not present): curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  2. Install Python dependencies: uv sync"
    echo "  3. Activate environment: source bin/activate.sh"
    exit 0
else
    echo "PASSED: All dependencies satisfied"
    echo ""
    echo "Next steps:"
    echo "  1. Install Python dependencies (if not done): uv sync"
    echo "  2. Activate environment:"
    echo "     - With direnv: direnv allow"
    echo "     - Without direnv: source bin/activate.sh"
    exit 0
fi
