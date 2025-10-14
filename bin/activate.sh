#!/bin/bash
# Mycelium Environment Activation Script
# Version: 1.0
# Manual activation for users without direnv

# Enable verbose mode if requested
if [ -n "$MYCELIUM_VERBOSE" ] || [ "$1" = "-v" ] || [ "$1" = "--verbose" ]; then
    set -x
    echo "Activation started at $(date)"
    echo "Working directory: $(pwd)"
    echo "Script location: ${BASH_SOURCE[0]}"
fi

# Check if already activated
if [ -n "$MYCELIUM_ENV_ACTIVE" ]; then
    echo "Warning: Mycelium environment already active" >&2
    echo "  Current MYCELIUM_ROOT: $MYCELIUM_ROOT" >&2
    echo "  Run 'deactivate' first if you want to re-activate" >&2
    return 1
fi

# Detect current shell and script location
if [ -n "$BASH_VERSION" ]; then
    CURRENT_SHELL="bash"
    SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [ -n "$ZSH_VERSION" ]; then
    CURRENT_SHELL="zsh"
    SCRIPT_PATH="${(%):-%N}"
else
    CURRENT_SHELL="unknown"
    echo "Warning: Shell detection failed" >&2
    echo "  Supported shells: bash, zsh" >&2
    echo "  Current shell: $SHELL" >&2
    echo "  This may cause issues. Continue? [y/N]" >&2
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        return 1
    fi
    # Fallback to $0 (may not work when sourced)
    SCRIPT_PATH="$0"
fi

# Detect script directory and calculate MYCELIUM_ROOT
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)" || {
    echo "Error: Failed to determine script directory" >&2
    return 1
}

export MYCELIUM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)" || {
    echo "Error: Failed to determine MYCELIUM_ROOT" >&2
    return 1
}

# Validate MYCELIUM_ROOT
if [ ! -d "$MYCELIUM_ROOT" ]; then
    echo "Error: MYCELIUM_ROOT directory does not exist: $MYCELIUM_ROOT" >&2
    return 1
fi

if [ ! -f "$MYCELIUM_ROOT/pyproject.toml" ]; then
    echo "Error: Not a Mycelium project (missing pyproject.toml)" >&2
    echo "  MYCELIUM_ROOT: $MYCELIUM_ROOT" >&2
    return 1
fi

# WSL detection and warning
if [ -f /proc/version ] && grep -qi microsoft /proc/version 2>/dev/null; then
    if [[ "$PWD" == /mnt/* ]]; then
        echo "Warning: You're in Windows filesystem (/mnt/c/)" >&2
        echo "  Performance will be poor. Consider moving project to WSL filesystem (~)" >&2
        echo "  Continue? [y/N]" >&2
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
fi

# Backup current environment for restoration
export MYCELIUM_OLD_PATH="$PATH"
export MYCELIUM_OLD_PS1="$PS1"

# Set XDG directories with proper fallbacks
export MYCELIUM_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/mycelium"
export MYCELIUM_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mycelium"
export MYCELIUM_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/mycelium"
export MYCELIUM_STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/mycelium"
export MYCELIUM_PROJECT_DIR="$MYCELIUM_ROOT/.mycelium"

# Create XDG directories if they don't exist
for dir in "$MYCELIUM_CONFIG_DIR" "$MYCELIUM_DATA_DIR" "$MYCELIUM_CACHE_DIR" "$MYCELIUM_STATE_DIR"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" || {
            echo "Error: Failed to create directory: $dir" >&2
            return 1
        }
    fi
done

# Modify PATH (prepend project bin)
export PATH="$MYCELIUM_ROOT/bin:$PATH"

# Activate Python virtual environment (if exists)
if [ -d "$MYCELIUM_ROOT/.venv" ]; then
    # Check if activation script exists
    if [ -f "$MYCELIUM_ROOT/.venv/bin/activate" ]; then
        source "$MYCELIUM_ROOT/.venv/bin/activate"
    else
        echo "Warning: .venv exists but activate script not found" >&2
    fi
else
    echo "Warning: Virtual environment not found at .venv/" >&2
    echo "  Run: uv sync" >&2
fi

# Modify shell prompt to indicate activation
if [ -n "$BASH_VERSION" ]; then
    export PS1="(mycelium) $PS1"
elif [ -n "$ZSH_VERSION" ]; then
    export PROMPT="(mycelium) $PROMPT"
fi

# Mark environment as active
export MYCELIUM_ENV_ACTIVE=1

# Define deactivate function
deactivate() {
    # Restore original PATH
    if [ -n "$MYCELIUM_OLD_PATH" ]; then
        export PATH="$MYCELIUM_OLD_PATH"
        unset MYCELIUM_OLD_PATH
    fi

    # Restore original prompt
    if [ -n "$MYCELIUM_OLD_PS1" ]; then
        export PS1="$MYCELIUM_OLD_PS1"
        unset MYCELIUM_OLD_PS1
    fi

    # Deactivate Python virtual environment
    if [ -n "$VIRTUAL_ENV" ] && command -v deactivate &> /dev/null; then
        command deactivate
    fi

    # Unset all Mycelium environment variables
    unset MYCELIUM_ROOT
    unset MYCELIUM_CONFIG_DIR
    unset MYCELIUM_DATA_DIR
    unset MYCELIUM_CACHE_DIR
    unset MYCELIUM_STATE_DIR
    unset MYCELIUM_PROJECT_DIR
    unset MYCELIUM_ENV_ACTIVE

    # Cleanup verification
    local issues=0

    if [ -n "$MYCELIUM_ENV_ACTIVE" ]; then
        echo "Warning: MYCELIUM_ENV_ACTIVE still set" >&2
        issues=$((issues + 1))
    fi

    if echo "$PATH" | grep -q "mycelium/bin"; then
        echo "Warning: Mycelium still in PATH" >&2
        issues=$((issues + 1))
    fi

    if [ $issues -gt 0 ]; then
        echo "Warning: Deactivation may be incomplete. Found $issues issues." >&2
        echo "  Try: exec $SHELL" >&2
    fi

    # Remove deactivate function itself
    unset -f deactivate

    echo "Mycelium environment deactivated"
}

# Display success message
echo "Mycelium environment activated (shell: $CURRENT_SHELL)"
echo "  MYCELIUM_ROOT: $MYCELIUM_ROOT"
echo "  Run 'deactivate' to deactivate"
