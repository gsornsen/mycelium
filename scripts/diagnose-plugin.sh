#!/usr/bin/env bash
# Diagnostic script for Mycelium plugin loading

echo "=== Mycelium Plugin Diagnostic ==="
echo ""

PLUGIN_PATH="/home/gerald/git/mycelium/plugins/mycelium-core"

echo "1. Plugin Structure:"
echo "   - plugin.json: $(test -f "$PLUGIN_PATH/.claude-plugin/plugin.json" && echo "✓" || echo "✗")"
echo "   - hooks.json: $(test -f "$PLUGIN_PATH/hooks/hooks.json" && echo "✓" || echo "✗")"
echo "   - agents/: $(test -d "$PLUGIN_PATH/agents" && echo "✓" || echo "✗")"
echo "   - commands/: $(test -d "$PLUGIN_PATH/commands" && echo "✓" || echo "✗")"
echo ""

echo "2. Agent Count:"
echo "   - Total .md files: $(find "$PLUGIN_PATH/agents" -maxdepth 1 -name "*.md" -type f | wc -l)"
echo ""

echo "3. Sample Agent Files:"
find "$PLUGIN_PATH/agents" -maxdepth 1 -name "*.md" -type f | head -3 | while read f; do
    echo "   - $(basename "$f")"
done
echo ""

echo "4. JSON Validation:"
python3 -c "import json; json.load(open('$PLUGIN_PATH/.claude-plugin/plugin.json'))" 2>&1 > /dev/null && echo "   - plugin.json: ✓ Valid" || echo "   - plugin.json: ✗ Invalid"
python3 -c "import json; json.load(open('$PLUGIN_PATH/hooks/hooks.json'))" 2>&1 > /dev/null && echo "   - hooks.json: ✓ Valid" || echo "   - hooks.json: ✗ Invalid"
echo ""

echo "5. Sample Agent Frontmatter:"
SAMPLE_AGENT=$(find "$PLUGIN_PATH/agents" -maxdepth 1 -name "*.md" -type f | head -1)
if [ -n "$SAMPLE_AGENT" ]; then
    echo "   From: $(basename "$SAMPLE_AGENT")"
    head -6 "$SAMPLE_AGENT" | grep -E "^(---|name:|description:)" | head -4
fi
echo ""

echo "6. Marketplace Config:"
echo "   Location: $(cat ~/.claude/plugins/known_marketplaces.json | jq -r '.mycelium.installLocation')"
echo "   Last Updated: $(cat ~/.claude/plugins/known_marketplaces.json | jq -r '.mycelium.lastUpdated')"
echo ""

echo "=== Diagnostic Complete ==="
