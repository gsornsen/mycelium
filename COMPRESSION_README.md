# Agent Description Compression Tool

This tool compresses agent descriptions in `index.json` while preserving all metadata and ensuring data integrity.

## Files

- **compress_descriptions.py** - Main compression script
- **compression_rules.json** - Configuration file for compression rules (to be populated by refactoring-specialist)

## Features

- Applies systematic compression rules to all agent descriptions
- Creates automatic backup of original index.json
- Validates data integrity (no metadata loss)
- Generates detailed before/after comparison report
- Supports dry-run mode for safe testing
- Configurable compression rules via JSON file

## Usage

### Dry Run (Recommended First)

Test compression without modifying files:

```bash
uv run python compress_descriptions.py --dry-run
```

This will:
- Load and validate index.json
- Apply compression rules
- Generate report showing projected savings
- NOT modify index.json (safe to run)

### Full Execution

Apply compression and update index.json:

```bash
uv run python compress_descriptions.py
```

This will:
- Create backup: `index.json.backup`
- Apply compression to all descriptions
- Validate results
- Update `index.json`
- Generate `compression-report.txt`

### Custom Paths

```bash
# Custom index.json location
uv run python compress_descriptions.py /path/to/index.json

# Custom rules file
uv run python compress_descriptions.py --rules /path/to/rules.json

# Both custom paths
uv run python compress_descriptions.py /path/to/index.json --rules /path/to/rules.json
```

## Compression Rules

The script reads compression rules from `compression_rules.json`. The refactoring-specialist should populate this file with optimized rules based on their analysis.

### Rule Types

1. **Remove Phrases** - Exact phrase removal
   ```json
   "remove_phrases": [
     "specializing in ",
     "with focus on "
   ]
   ```

2. **Replace Patterns** - Regex pattern replacement
   ```json
   "replace_patterns": [
     {
       "pattern": "\\bspecializing in\\b",
       "replacement": "",
       "description": "Remove redundant specialization phrase"
     }
   ]
   ```

3. **Word Replacements** - Replace verbose terms with concise alternatives
   ```json
   "word_replacements": [
     {
       "from": "implementation",
       "to": "impl",
       "context": "Technical documentation"
     }
   ]
   ```

4. **Settings** - Global compression settings
   ```json
   "settings": {
     "preserve_meaning": true,
     "preserve_technical_terms": true,
     "max_description_length": 150,
     "target_reduction_percent": 20
   }
   ```

## Validation

The script performs comprehensive validation:

- JSON structure integrity
- Agent count preservation
- No empty descriptions
- All metadata unchanged (tools, keywords, categories, etc.)
- Only description field modified

If validation fails, the original file is preserved.

## Output Files

### index.json.backup
Complete backup of original index.json created before any modifications.

### compression-report.txt
Detailed report including:
- Overall statistics (tokens saved, reduction percentage)
- Top 10 agents by token savings
- Agents with minimal compression
- Before/after comparison for every agent
- Compression rules applied

## Example Workflow

1. **Initial Analysis** (Dry Run)
   ```bash
   uv run python compress_descriptions.py --dry-run
   ```
   Review `compression-report.txt` to see projected results.

2. **Apply Compression**
   ```bash
   uv run python compress_descriptions.py
   ```
   Creates backup and updates index.json.

3. **Verify Results**
   - Check `compression-report.txt` for statistics
   - Validate `index.json` loads correctly
   - Review sample descriptions for quality

4. **Rollback if Needed**
   ```bash
   cp plugins/mycelium-core/agents/index.json.backup plugins/mycelium-core/agents/index.json
   ```

## Safety Features

- **Automatic Backup** - Original file always preserved
- **Validation** - Multi-step validation before writing
- **Dry Run Mode** - Test without modification
- **Error Handling** - Graceful failure with preserved data
- **Detailed Reporting** - Complete audit trail of changes

## Token Estimation

Token counts use a rough approximation (1 token ≈ 4 characters). For precise token counts, consider using a proper tokenizer.

## Integration with Refactoring-Specialist

The refactoring-specialist should:

1. Analyze current descriptions using data-analyst results
2. Identify compression opportunities
3. Create optimized compression rules
4. Update `compression_rules.json` with their strategy
5. Test with dry-run mode
6. Review and approve final compression

## Requirements

- Python 3.7+
- Standard library only (json, re, shutil, pathlib)
- No external dependencies
