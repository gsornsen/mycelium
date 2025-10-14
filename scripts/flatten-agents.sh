#!/usr/bin/env bash
# Flatten agents directory structure for Claude Code compatibility
# Claude Code only loads agents directly from agents/ directory, not subdirectories

set -euo pipefail

PLUGIN_DIR="/home/gerald/git/mycelium/plugins/mycelium-core"
AGENTS_DIR="${PLUGIN_DIR}/agents"
BACKUP_DIR="${PLUGIN_DIR}/agents.backup"

echo "Flattening Mycelium agents directory for Claude Code compatibility..."

# Create backup
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup at ${BACKUP_DIR}..."
    cp -r "$AGENTS_DIR" "$BACKUP_DIR"
else
    echo "Backup already exists at ${BACKUP_DIR}, skipping..."
fi

# Find all .md files in subdirectories and move them up
echo "Moving agent files to top-level agents/ directory..."

find "$AGENTS_DIR" -mindepth 2 -type f -name "*.md" | while read -r file; do
    # Get the relative path from agents/
    rel_path="${file#${AGENTS_DIR}/}"

    # Get the subdirectory name (e.g., "01-core-development")
    subdir=$(dirname "$rel_path")

    # Get just the filename
    filename=$(basename "$file")

    # Skip README files in subdirectories
    if [ "$filename" = "README.md" ]; then
        echo "Skipping: $rel_path"
        continue
    fi

    # Create new filename with category prefix
    # e.g., "01-core-development/api-designer.md" -> "01-core-api-designer.md"
    category_prefix=$(echo "$subdir" | cut -d'/' -f1 | cut -d'-' -f1-2)
    new_filename="${category_prefix}-${filename}"

    # Move the file
    echo "Moving: $rel_path -> agents/${new_filename}"
    mv "$file" "${AGENTS_DIR}/${new_filename}"
done

# Remove empty subdirectories (keep README.md files at top level)
echo "Cleaning up empty subdirectories..."
find "$AGENTS_DIR" -mindepth 1 -type d -empty -delete

# Remove subdirectories that only contain README.md
find "$AGENTS_DIR" -mindepth 1 -type d | while read -r dir; do
    if [ $(find "$dir" -type f | wc -l) -eq 1 ] && [ -f "$dir/README.md" ]; then
        echo "Removing subdirectory with only README: $dir"
        rm -rf "$dir"
    fi
done

echo ""
echo "Done! Agent files have been flattened."
echo "Original structure backed up to: ${BACKUP_DIR}"
echo ""
echo "Agent count: $(find "$AGENTS_DIR" -maxdepth 1 -name "*.md" -type f | wc -l)"
echo ""
echo "You may need to restart Claude Code for changes to take effect."
