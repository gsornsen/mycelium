# Source: projects/onboarding/milestones/M10_POLISH_RELEASE.md
# Line: 867
# Valid syntax: True
# Has imports: True
# Has assignments: True

# scripts/generate_changelog.py
"""Generate changelog from git commits."""

import re
import subprocess
import sys
from datetime import datetime


def get_commits_since_last_tag() -> list[str]:
    """Get commits since last release tag."""
    # Get last tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        last_tag = result.stdout.strip()
        commit_range = f"{last_tag}..HEAD"
    else:
        # No previous tags, get all commits
        commit_range = "HEAD"

    # Get commits
    result = subprocess.run(
        ["git", "log", commit_range, "--pretty=format:%H|%s|%an|%ad"],
        capture_output=True,
        text=True
    )

    return result.stdout.strip().split('\n') if result.stdout else []


def parse_commit(commit_line: str) -> dict[str, str]:
    """Parse commit line into structured data."""
    parts = commit_line.split('|')
    return {
        'hash': parts[0][:7],
        'subject': parts[1],
        'author': parts[2],
        'date': parts[3],
    }


def categorize_commits(commits: list[dict]) -> dict[str, list[dict]]:
    """Categorize commits by type (feat, fix, docs, etc.)."""
    categories = {
        'Features': [],
        'Bug Fixes': [],
        'Documentation': [],
        'Performance': [],
        'Refactoring': [],
        'Testing': [],
        'Chores': [],
        'Other': [],
    }

    for commit in commits:
        subject = commit['subject']

        if re.match(r'^feat(\(.*\))?:', subject):
            categories['Features'].append(commit)
        elif re.match(r'^fix(\(.*\))?:', subject):
            categories['Bug Fixes'].append(commit)
        elif re.match(r'^docs(\(.*\))?:', subject):
            categories['Documentation'].append(commit)
        elif re.match(r'^perf(\(.*\))?:', subject):
            categories['Performance'].append(commit)
        elif re.match(r'^refactor(\(.*\))?:', subject):
            categories['Refactoring'].append(commit)
        elif re.match(r'^test(\(.*\))?:', subject):
            categories['Testing'].append(commit)
        elif re.match(r'^chore(\(.*\))?:', subject):
            categories['Chores'].append(commit)
        else:
            categories['Other'].append(commit)

    return categories


def generate_changelog(version: str) -> str:
    """Generate changelog in markdown format."""
    today = datetime.now().strftime('%Y-%m-%d')

    changelog = f"# Release {version}\n\n"
    changelog += f"**Release Date**: {today}\n\n"

    # Get and parse commits
    commit_lines = get_commits_since_last_tag()
    commits = [parse_commit(line) for line in commit_lines if line]

    if not commits:
        changelog += "No changes since last release.\n"
        return changelog

    # Categorize
    categories = categorize_commits(commits)

    # Generate sections
    for category, commits_in_category in categories.items():
        if not commits_in_category:
            continue

        changelog += f"## {category}\n\n"

        for commit in commits_in_category:
            # Clean up commit subject (remove conventional commit prefix)
            subject = re.sub(r'^[a-z]+(\(.*\))?:\s*', '', commit['subject'])
            changelog += f"- {subject} ([{commit['hash']}](https://github.com/your-org/mycelium/commit/{commit['hash']}))\n"

        changelog += "\n"

    # Add contributors
    contributors = sorted(set(c['author'] for c in commits))
    changelog += "## Contributors\n\n"
    changelog += "Thank you to all contributors:\n\n"
    for contributor in contributors:
        changelog += f"- @{contributor}\n"

    return changelog


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_changelog.py <version>")
        sys.exit(1)

    version = sys.argv[1]
    changelog = generate_changelog(version)

    print(changelog)


if __name__ == "__main__":
    main()
