#!/usr/bin/env python3
"""Agent Description Compression Script

Compresses agent descriptions in index.json while preserving all metadata.
Creates backup and generates detailed compression report.
"""

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class DescriptionCompressor:
    """Handles compression of agent descriptions with validation and reporting."""

    def __init__(self, index_path: str, rules_path: str | None = None):
        """Initialize compressor with path to index.json.

        Args:
            index_path: Path to the index.json file
            rules_path: Optional path to compression rules JSON file
        """
        self.index_path = Path(index_path)
        self.backup_path = Path(f"{index_path}.backup")
        self.report_path = Path(index_path).parent / "compression-report.txt"

        # Rules configuration
        if rules_path:
            self.rules_path = Path(rules_path)
        else:
            self.rules_path = Path(index_path).parent.parent.parent / "compression_rules.json"

        self.compression_rules: dict[str, Any] = {}
        self.original_data: dict[str, Any] = {}
        self.compressed_data: dict[str, Any] = {}
        self.compression_stats: list[dict[str, Any]] = []

    def load_index(self) -> bool:
        """Load the index.json file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.index_path, encoding='utf-8') as f:
                self.original_data = json.load(f)
            print(f"✓ Loaded {self.index_path}")
            print(f"  Found {self.original_data.get('agent_count', 0)} agents")
            return True
        except FileNotFoundError:
            print(f"✗ Error: File not found: {self.index_path}", file=sys.stderr)
            return False
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON in {self.index_path}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"✗ Error loading file: {e}", file=sys.stderr)
            return False

    def load_compression_rules(self) -> bool:
        """Load compression rules from JSON file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.rules_path.exists():
                with open(self.rules_path, encoding='utf-8') as f:
                    self.compression_rules = json.load(f)
                print(f"✓ Loaded compression rules from {self.rules_path}")
                return True
            print(f"⚠ No rules file found at {self.rules_path}")
            print("  Using default compression rules")
            self.compression_rules = self._get_default_rules()
            return True
        except Exception as e:
            print(f"✗ Error loading rules: {e}", file=sys.stderr)
            print("  Using default compression rules")
            self.compression_rules = self._get_default_rules()
            return True

    def _get_default_rules(self) -> dict[str, Any]:
        """Get default compression rules.

        Returns:
            Dictionary of default compression rules
        """
        return {
            "rules": {
                "remove_phrases": [
                    "specializing in ",
                    "with focus on ",
                    "focusing on ",
                ],
                "replace_patterns": [],
                "word_replacements": [],
                "structural_rules": []
            },
            "settings": {
                "preserve_meaning": True,
                "preserve_technical_terms": True,
                "max_description_length": None,
                "target_reduction_percent": None
            }
        }

    def create_backup(self) -> bool:
        """Create backup of original index.json.

        Returns:
            True if successful, False otherwise
        """
        try:
            shutil.copy2(self.index_path, self.backup_path)
            print(f"✓ Created backup: {self.backup_path}")
            return True
        except Exception as e:
            print(f"✗ Error creating backup: {e}", file=sys.stderr)
            return False

    def compress_description(self, description: str, agent_name: str) -> str:
        """Apply compression rules to a single description.

        This method implements the compression strategy provided by refactoring-specialist.

        Args:
            description: Original description text
            agent_name: Name of the agent (for context-aware compression)

        Returns:
            Compressed description
        """
        if not description:
            return description

        compressed = description
        rules = self.compression_rules.get('rules', {})

        # Apply phrase removal
        remove_phrases = rules.get('remove_phrases', [])
        for phrase in remove_phrases:
            compressed = compressed.replace(phrase, " ")

        # Apply pattern replacements (regex)
        replace_patterns = rules.get('replace_patterns', [])
        for pattern_rule in replace_patterns:
            pattern = pattern_rule.get('pattern', '')
            replacement = pattern_rule.get('replacement', '')
            if pattern:
                try:
                    compressed = re.sub(pattern, replacement, compressed)
                except re.error as e:
                    print(f"  ⚠ Warning: Invalid regex pattern '{pattern}': {e}")

        # Apply word replacements
        word_replacements = rules.get('word_replacements', [])
        for replacement in word_replacements:
            from_word = replacement.get('from', '')
            to_word = replacement.get('to', '')
            if from_word and to_word:
                # Use word boundaries for accurate replacement
                pattern = r'\b' + re.escape(from_word) + r'\b'
                compressed = re.sub(pattern, to_word, compressed, flags=re.IGNORECASE)

        # Clean up multiple spaces
        compressed = re.sub(r'\s+', ' ', compressed)

        # Trim whitespace
        compressed = compressed.strip()

        # Apply length limit if specified
        settings = self.compression_rules.get('settings', {})
        max_length = settings.get('max_description_length')
        if max_length and len(compressed) > max_length:
            # Truncate at last sentence within limit
            truncated = compressed[:max_length]
            last_period = truncated.rfind('.')
            if last_period > 0:
                compressed = truncated[:last_period + 1]
            else:
                compressed = truncated.rstrip() + "..."

        return compressed

    def compress_all_descriptions(self) -> bool:
        """Compress descriptions for all agents.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Deep copy the original data
            self.compressed_data = json.loads(json.dumps(self.original_data))

            agents = self.compressed_data.get('agents', [])
            if not agents:
                print("✗ No agents found in index.json", file=sys.stderr)
                return False

            print(f"\nCompressing {len(agents)} agent descriptions...")

            for i, agent in enumerate(agents, 1):
                agent_name = agent.get('name', 'unknown')
                original_desc = agent.get('description', '')

                if not original_desc:
                    print(f"  ⚠ Warning: Agent '{agent_name}' has no description")
                    continue

                # Apply compression
                compressed_desc = self.compress_description(original_desc, agent_name)

                # Update agent description
                agent['description'] = compressed_desc

                # Calculate token estimates (rough approximation: 1 token ≈ 4 chars)
                original_tokens = len(original_desc) // 4
                compressed_tokens = len(compressed_desc) // 4
                saved_tokens = original_tokens - compressed_tokens

                # Store statistics
                self.compression_stats.append({
                    'agent_name': agent_name,
                    'original_length': len(original_desc),
                    'compressed_length': len(compressed_desc),
                    'original_tokens': original_tokens,
                    'compressed_tokens': compressed_tokens,
                    'saved_tokens': saved_tokens,
                    'reduction_percent': (saved_tokens / original_tokens * 100) if original_tokens > 0 else 0,
                    'original_text': original_desc,
                    'compressed_text': compressed_desc
                })

                if (i % 20) == 0:
                    print(f"  Processed {i}/{len(agents)} agents...")

            print("✓ Compressed all descriptions")
            return True

        except Exception as e:
            print(f"✗ Error during compression: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def validate_compressed_data(self) -> bool:
        """Validate the compressed data for integrity.

        Returns:
            True if validation passes, False otherwise
        """
        print("\nValidating compressed data...")

        validation_errors = []

        # Check JSON structure
        try:
            json.dumps(self.compressed_data)
        except Exception as e:
            validation_errors.append(f"Invalid JSON structure: {e}")

        # Verify agent count
        original_count = len(self.original_data.get('agents', []))
        compressed_count = len(self.compressed_data.get('agents', []))

        if original_count != compressed_count:
            validation_errors.append(
                f"Agent count mismatch: {original_count} vs {compressed_count}"
            )

        # Verify all agents have descriptions
        agents_without_desc = []
        for agent in self.compressed_data.get('agents', []):
            desc = agent.get('description', '').strip()
            if not desc:
                agents_without_desc.append(agent.get('name', 'unknown'))

        if agents_without_desc:
            validation_errors.append(
                f"Agents without descriptions: {', '.join(agents_without_desc)}"
            )

        # Verify metadata preservation
        for i, (orig, comp) in enumerate(zip(
            self.original_data.get('agents', []),
            self.compressed_data.get('agents', []), strict=False
        )):
            metadata_fields = ['id', 'name', 'display_name', 'category', 'tools',
                             'keywords', 'file_path', 'estimated_tokens']

            for field in metadata_fields:
                if field in orig and orig.get(field) != comp.get(field):
                    validation_errors.append(
                        f"Agent {i}: Metadata field '{field}' was modified"
                    )

        # Print validation results
        if validation_errors:
            print("✗ Validation failed:")
            for error in validation_errors:
                print(f"  - {error}")
            return False
        print("✓ Validation passed")
        print("  - JSON structure valid")
        print("  - Agent count preserved")
        print("  - All agents have descriptions")
        print("  - Metadata unchanged")
        return True

    def write_compressed_index(self) -> bool:
        """Write the compressed data to index.json.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(self.compressed_data, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Written compressed data to {self.index_path}")
            return True
        except Exception as e:
            print(f"✗ Error writing compressed file: {e}", file=sys.stderr)
            return False

    def generate_report(self) -> bool:
        """Generate detailed compression report.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("AGENT DESCRIPTION COMPRESSION REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Index file: {self.index_path}\n")
                f.write(f"Backup file: {self.backup_path}\n")
                f.write(f"Rules file: {self.rules_path}\n")
                f.write("\n")

                # Compression rules summary
                f.write("-" * 80 + "\n")
                f.write("COMPRESSION RULES APPLIED\n")
                f.write("-" * 80 + "\n")

                rules = self.compression_rules.get('rules', {})
                settings = self.compression_rules.get('settings', {})

                f.write(f"Remove phrases: {len(rules.get('remove_phrases', []))}\n")
                f.write(f"Replace patterns: {len(rules.get('replace_patterns', []))}\n")
                f.write(f"Word replacements: {len(rules.get('word_replacements', []))}\n")
                f.write(f"Structural rules: {len(rules.get('structural_rules', []))}\n")
                f.write("\nSettings:\n")
                for key, value in settings.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")

                # Overall statistics
                total_original_tokens = sum(s['original_tokens'] for s in self.compression_stats)
                total_compressed_tokens = sum(s['compressed_tokens'] for s in self.compression_stats)
                total_saved = total_original_tokens - total_compressed_tokens

                f.write("-" * 80 + "\n")
                f.write("OVERALL STATISTICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total agents processed: {len(self.compression_stats)}\n")
                f.write(f"Original token count: {total_original_tokens:,}\n")
                f.write(f"Compressed token count: {total_compressed_tokens:,}\n")
                f.write(f"Tokens saved: {total_saved:,}\n")
                if total_original_tokens > 0:
                    f.write(f"Average reduction: {(total_saved/total_original_tokens*100):.2f}%\n")
                f.write("\n")

                # Distribution statistics
                if self.compression_stats:
                    reductions = [s['reduction_percent'] for s in self.compression_stats]
                    f.write(f"Min reduction: {min(reductions):.2f}%\n")
                    f.write(f"Max reduction: {max(reductions):.2f}%\n")
                    f.write(f"Median reduction: {sorted(reductions)[len(reductions)//2]:.2f}%\n")
                    f.write("\n")

                # Top savings
                f.write("-" * 80 + "\n")
                f.write("TOP 10 AGENTS BY TOKEN SAVINGS\n")
                f.write("-" * 80 + "\n")

                sorted_stats = sorted(self.compression_stats,
                                    key=lambda x: x['saved_tokens'],
                                    reverse=True)

                for i, stat in enumerate(sorted_stats[:10], 1):
                    f.write(f"{i}. {stat['agent_name']}\n")
                    f.write(f"   Saved: {stat['saved_tokens']} tokens ({stat['reduction_percent']:.1f}%)\n")
                    f.write(f"   {stat['original_tokens']} → {stat['compressed_tokens']} tokens\n")
                    f.write("\n")

                # Agents with minimal/no compression
                f.write("-" * 80 + "\n")
                f.write("AGENTS WITH MINIMAL COMPRESSION (<5% reduction)\n")
                f.write("-" * 80 + "\n")

                minimal_compression = [s for s in self.compression_stats if s['reduction_percent'] < 5]
                if minimal_compression:
                    for stat in sorted(minimal_compression, key=lambda x: x['reduction_percent']):
                        f.write(f"- {stat['agent_name']}: {stat['reduction_percent']:.1f}% reduction\n")
                else:
                    f.write("None - all agents had >5% compression\n")
                f.write("\n")

                # Detailed comparison
                f.write("-" * 80 + "\n")
                f.write("DETAILED BEFORE/AFTER COMPARISON\n")
                f.write("-" * 80 + "\n")

                for stat in sorted(self.compression_stats, key=lambda x: x['agent_name']):
                    f.write(f"\nAgent: {stat['agent_name']}\n")
                    f.write(f"Tokens: {stat['original_tokens']} → {stat['compressed_tokens']} "
                           f"(saved {stat['saved_tokens']}, {stat['reduction_percent']:.1f}%)\n")
                    f.write(f"\nBEFORE ({len(stat['original_text'])} chars):\n")
                    f.write(f"{stat['original_text']}\n")
                    f.write(f"\nAFTER ({len(stat['compressed_text'])} chars):\n")
                    f.write(f"{stat['compressed_text']}\n")
                    f.write("-" * 80 + "\n")

            print(f"✓ Generated report: {self.report_path}")

            # Print summary to console
            print("\n" + "=" * 80)
            print("COMPRESSION SUMMARY")
            print("=" * 80)
            print(f"Agents processed: {len(self.compression_stats)}")
            print(f"Original tokens: {total_original_tokens:,}")
            print(f"Compressed tokens: {total_compressed_tokens:,}")
            print(f"Tokens saved: {total_saved:,} ({(total_saved/total_original_tokens*100):.2f}%)" if total_original_tokens > 0 else "Tokens saved: 0")
            print("=" * 80)

            return True

        except Exception as e:
            print(f"✗ Error generating report: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def run(self, dry_run: bool = False) -> bool:
        """Execute the complete compression workflow.

        Args:
            dry_run: If True, only generate report without modifying files

        Returns:
            True if successful, False otherwise
        """
        print("Starting agent description compression...")
        print()

        # Step 1: Load index
        if not self.load_index():
            return False

        # Step 2: Load compression rules
        if not self.load_compression_rules():
            return False

        # Step 3: Create backup
        if not dry_run:
            if not self.create_backup():
                return False
        else:
            print("⚠ DRY RUN MODE - No backup created")

        # Step 4: Compress descriptions
        if not self.compress_all_descriptions():
            return False

        # Step 5: Validate
        if not self.validate_compressed_data():
            print("\n✗ Validation failed. Original file preserved.")
            return False

        # Step 6: Write compressed file (unless dry run)
        if not dry_run:
            if not self.write_compressed_index():
                return False
        else:
            print("\n⚠ DRY RUN MODE - Compressed file NOT written")

        # Step 7: Generate report
        if not self.generate_report():
            return False

        if dry_run:
            print("\n✓ Dry run completed successfully!")
            print("  Review the report to see compression results.")
            print("  Run without --dry-run to apply changes.")
        else:
            print("\n✓ Compression completed successfully!")

        return True


def main():
    """Main entry point."""
    # Default path to index.json
    default_path = "/home/gerald/git/mycelium/plugins/mycelium-core/agents/index.json"

    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    # Find index path from arguments
    index_path = default_path
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            index_path = arg
            break

    # Find rules path from arguments
    rules_path = None
    if '--rules' in sys.argv:
        rules_idx = sys.argv.index('--rules')
        if rules_idx + 1 < len(sys.argv):
            rules_path = sys.argv[rules_idx + 1]

    # Create and run compressor
    compressor = DescriptionCompressor(index_path, rules_path)
    success = compressor.run(dry_run=dry_run)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
