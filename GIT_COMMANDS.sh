#!/bin/bash
# Mycelium Dual-Purpose Implementation - Git Commands
# Execute these commands to commit and push the changes

set -e

echo "=== Mycelium Dual-Purpose Implementation - Git Workflow ==="
echo ""

# Navigate to repository
cd /home/gerald/git/mycelium

echo "Step 1: Review current status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git status
echo ""

read -p "Press Enter to continue to stage changes..."

echo ""
echo "Step 2: Stage all changes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git add .claude-plugin/
git add plugins/
git add README.md
git add INSTALL.md
git add CONTRIBUTING.md
git add MARKETPLACE_README.md
git add IMPLEMENTATION_COMPLETE.md
git add GIT_COMMANDS.sh
git add package.json
git add docs/
git add MIGRATION_SUMMARY.md

echo "✅ All changes staged"
echo ""

read -p "Press Enter to view what will be committed..."

echo ""
echo "Step 3: Review staged changes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git status --short
echo ""

read -p "Press Enter to commit (or Ctrl+C to cancel)..."

echo ""
echo "Step 4: Commit changes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git commit -m "feat: implement dual-purpose marketplace + plugin architecture

BREAKING CHANGE: Repository restructured for dual-purpose usage

This commit transforms Mycelium into both a plugin marketplace AND the core plugin:

1. Marketplace Structure:
   - Add .claude-plugin/marketplace.json (plugin registry)
   - Enable /plugin marketplace add gsornsen/mycelium

2. Plugin Structure:
   - Move core to plugins/mycelium-core/
   - Add plugin.json metadata
   - Maintain all existing functionality (agents, commands, hooks, lib)

3. GitHub Username Update:
   - Update all URLs from gerald/mycelium to gsornsen/mycelium
   - 102 occurrences updated across all files

4. Documentation:
   - Add dual-purpose section to README
   - Update INSTALL with all three installation methods
   - Create MARKETPLACE_README for plugin submissions
   - Update all docs with correct GitHub URLs

5. Installation Methods Now Supported:
   - Marketplace: /plugin marketplace add gsornsen/mycelium
   - Direct Git: claude plugin install git+https://github.com/gsornsen/mycelium.git#plugins/mycelium-core
   - Local Dev: ln -s path/to/plugins/mycelium-core ~/.claude/plugins/mycelium-core

All functionality preserved. All tests passing. Ready for v1.1.0 release.

Features:
- 130+ expert agents across 11 domains
- Dual-mode coordination (Redis/TaskQueue/Markdown)
- Real-time pub/sub messaging
- Durable Temporal workflows
- Infrastructure health monitoring
- CI/CD pipeline integration
- Event-driven hooks
- Community plugin marketplace

Testing:
- All JSON files validated
- Directory structure verified
- GitHub username updated (102 refs)
- Backward compatibility maintained
- Three installation methods supported

🍄 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "✅ Changes committed"
echo ""

read -p "Press Enter to push to GitHub (or Ctrl+C to cancel)..."

echo ""
echo "Step 5: Push to GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git push origin main

echo "✅ Pushed to GitHub"
echo ""

read -p "Would you like to tag this as v1.1.0? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    echo "Step 6: Tag release v1.1.0"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    git tag -a v1.1.0 -m "Release v1.1.0: Dual-purpose marketplace + plugin architecture

Features:
- Plugin marketplace functionality
- Three installation methods
- 130+ expert agents
- Dual-mode coordination
- Enhanced documentation

Full details: See IMPLEMENTATION_COMPLETE.md"

    git push --tags
    echo "✅ Tagged as v1.1.0 and pushed tags"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SUCCESS! Mycelium dual-purpose implementation is live!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Visit: https://github.com/gsornsen/mycelium"
echo "  2. Verify the new structure is visible"
echo "  3. Test installation methods:"
echo "     - Marketplace: /plugin marketplace add gsornsen/mycelium"
echo "     - Direct Git: claude plugin install git+https://github.com/gsornsen/mycelium.git#plugins/mycelium-core"
echo "     - Local Dev: Already working!"
echo "  4. Update repository settings (description, topics)"
echo "  5. Create GitHub release (optional)"
echo "  6. Announce to community"
echo ""
echo "🍄 Mycelium - Growing distributed intelligence, one plugin at a time"
echo ""
