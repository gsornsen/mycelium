#!/usr/bin/env python3
"""Agent Description Analyzer
Analyzes agent descriptions for statistics and compression opportunities.
"""

import json
import re
import statistics
from collections import Counter


# Simple token estimator (approximation: 1 token ≈ 4 characters)
def estimate_tokens(text: str) -> int:
    """Estimate token count using character-based approximation."""
    return len(text) // 4

def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())

def extract_common_phrases(descriptions: list[str], min_length: int = 3) -> Counter:
    """Extract common n-gram phrases across descriptions."""
    phrases = Counter()

    for desc in descriptions:
        # Extract 3-word, 4-word, and 5-word phrases
        words = desc.lower().split()
        for n in range(min_length, 6):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                if len(phrase) > 10:  # Only count substantial phrases
                    phrases[phrase] += 1

    # Only return phrases that appear in multiple descriptions
    return Counter({phrase: count for phrase, count in phrases.items() if count > 1})

def identify_filler_words(text: str) -> list[str]:
    """Identify common filler words and phrases."""
    filler_patterns = [
        r'\bvery\b', r'\breally\b', r'\bquite\b', r'\bjust\b',
        r'\bactually\b', r'\bbasically\b', r'\bessentially\b',
        r'\bin order to\b', r'\bfor the purpose of\b',
        r'\bdue to the fact that\b', r'\bat this point in time\b',
        r'\bat the present time\b', r'\bfor the most part\b',
        r'\bin the event that\b', r'\bin my opinion\b',
        r'\bit is important to note that\b', r'\bwith the exception of\b'
    ]

    found = []
    for pattern in filler_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        found.extend([m.group() for m in matches])

    return found

def calculate_compression_potential(text: str) -> tuple[str, int, list[str]]:
    """Calculate compression potential based on various factors.
    Returns: (category, score, reasons)
    """
    score = 0
    reasons = []

    # Factor 1: Length (longer = more potential)
    if len(text) > 500:
        score += 30
        reasons.append(f"Long description ({len(text)} chars)")
    elif len(text) > 300:
        score += 20
        reasons.append(f"Medium-length description ({len(text)} chars)")

    # Factor 2: Filler words
    fillers = identify_filler_words(text)
    if fillers:
        score += len(fillers) * 5
        reasons.append(f"{len(fillers)} filler words/phrases")

    # Factor 3: Word density (words per sentence)
    sentences = len(re.split(r'[.!?]+', text))
    words = count_words(text)
    if sentences > 0:
        words_per_sentence = words / sentences
        if words_per_sentence > 25:
            score += 20
            reasons.append(f"Long sentences (avg {words_per_sentence:.1f} words)")

    # Factor 4: Redundant phrases (e.g., "and also", "in order to")
    redundant = re.findall(r'\band also\b|\bin order to\b|\bfor the purpose of\b', text, re.IGNORECASE)
    if redundant:
        score += len(redundant) * 3
        reasons.append(f"{len(redundant)} redundant phrases")

    # Factor 5: Excessive punctuation or formatting
    special_chars = len(re.findall(r'[;:,\-\(\)\[\]]', text))
    if special_chars > len(text) / 20:  # More than 5% special chars
        score += 10
        reasons.append(f"Heavy punctuation ({special_chars} chars)")

    # Categorize
    if score >= 50:
        category = "HIGH"
    elif score >= 25:
        category = "MEDIUM"
    else:
        category = "LOW"

    return category, score, reasons

def analyze_agents(filepath: str) -> dict:
    """Main analysis function."""
    print(f"Loading agents from {filepath}...")
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    # Extract agents array from the data structure
    agents_data = data.get('agents', [])
    print(f"Found {len(agents_data)} agents in the file")

    # Extract descriptions
    agents = []
    for agent_data in agents_data:
        description = agent_data.get('description', '')
        agents.append({
            'id': agent_data.get('id', 'unknown'),
            'name': agent_data.get('name', agent_data.get('id', 'unknown')),
            'description': description,
            'char_count': len(description),
            'word_count': count_words(description),
            'estimated_tokens': estimate_tokens(description),
        })

    # Calculate statistics
    total_agents = len(agents)
    total_chars = sum(a['char_count'] for a in agents)
    total_tokens = sum(a['estimated_tokens'] for a in agents)

    avg_chars = total_chars / total_agents if total_agents > 0 else 0
    avg_tokens = total_tokens / total_agents if total_agents > 0 else 0

    char_counts = [a['char_count'] for a in agents]
    median_chars = statistics.median(char_counts) if char_counts else 0

    # Find longest and shortest
    sorted_by_length = sorted(agents, key=lambda x: x['char_count'], reverse=True)
    longest = sorted_by_length[:10]
    shortest = sorted_by_length[-10:]

    # Extract common keywords
    all_descriptions = ' '.join([a['description'] for a in agents])
    words = re.findall(r'\b\w+\b', all_descriptions.lower())
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
                  'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
                  'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'}
    keywords = Counter([w for w in words if len(w) > 3 and w not in stop_words])

    # Find common phrases
    descriptions_list = [a['description'] for a in agents]
    common_phrases = extract_common_phrases(descriptions_list)

    # Analyze compression potential
    for agent in agents:
        category, score, reasons = calculate_compression_potential(agent['description'])
        agent['compression_category'] = category
        agent['compression_score'] = score
        agent['compression_reasons'] = reasons

    # Categorize agents
    high_compression = [a for a in agents if a['compression_category'] == 'HIGH']
    medium_compression = [a for a in agents if a['compression_category'] == 'MEDIUM']
    low_compression = [a for a in agents if a['compression_category'] == 'LOW']

    # Sort by compression score
    high_compression.sort(key=lambda x: x['compression_score'], reverse=True)
    medium_compression.sort(key=lambda x: x['compression_score'], reverse=True)

    return {
        'statistics': {
            'total_agents': total_agents,
            'total_chars': total_chars,
            'total_tokens': total_tokens,
            'avg_chars': avg_chars,
            'avg_tokens': avg_tokens,
            'median_chars': median_chars,
        },
        'longest': longest,
        'shortest': shortest,
        'keywords': keywords.most_common(30),
        'common_phrases': common_phrases.most_common(20),
        'compression_categories': {
            'high': high_compression,
            'medium': medium_compression,
            'low': low_compression,
        }
    }

def print_report(results: dict):
    """Print comprehensive analysis report."""
    stats = results['statistics']

    print("\n" + "="*80)
    print("AGENT DESCRIPTION ANALYSIS REPORT")
    print("="*80)

    # Section 1: Statistics
    print("\n1. CURRENT STATISTICS")
    print("-" * 80)
    print(f"Total Agents: {stats['total_agents']}")
    print(f"Total Characters: {stats['total_chars']:,}")
    print(f"Total Estimated Tokens: {stats['total_tokens']:,}")
    print("\nAverage Description Length:")
    print(f"  - Characters: {stats['avg_chars']:.1f}")
    print(f"  - Estimated Tokens: {stats['avg_tokens']:.1f}")
    print(f"  - Median Characters: {stats['median_chars']:.1f}")

    # Section 2: Extremes
    print("\n2. LENGTH EXTREMES")
    print("-" * 80)
    print("\nLongest Descriptions (Top 10):")
    for i, agent in enumerate(results['longest'], 1):
        print(f"{i:2d}. {agent['name'][:50]:50s} | {agent['char_count']:5d} chars | ~{agent['estimated_tokens']:4d} tokens")

    print("\nShortest Descriptions (Bottom 10):")
    for i, agent in enumerate(results['shortest'], 1):
        print(f"{i:2d}. {agent['name'][:50]:50s} | {agent['char_count']:5d} chars | ~{agent['estimated_tokens']:4d} tokens")

    # Section 3: Common Patterns
    print("\n3. COMMON PATTERNS & KEYWORDS")
    print("-" * 80)
    print("\nTop Keywords (excluding stop words):")
    for keyword, count in results['keywords'][:20]:
        print(f"  {keyword:20s}: {count:3d} occurrences")

    print("\nCommon Phrases (appearing in multiple descriptions):")
    for phrase, count in results['common_phrases'][:15]:
        print(f"  [{count:2d}x] {phrase}")

    # Section 4: Compression Potential
    print("\n4. COMPRESSION POTENTIAL ANALYSIS")
    print("-" * 80)

    high = results['compression_categories']['high']
    medium = results['compression_categories']['medium']
    low = results['compression_categories']['low']

    print(f"\nHigh Compression Potential: {len(high)} agents")
    print(f"Medium Compression Potential: {len(medium)} agents")
    print(f"Low Compression Potential: {len(low)} agents")

    print("\n5. TOP 10 MOST VERBOSE DESCRIPTIONS")
    print("-" * 80)

    all_agents = high + medium + low
    all_agents.sort(key=lambda x: x['compression_score'], reverse=True)

    for i, agent in enumerate(all_agents[:10], 1):
        print(f"\n{i}. {agent['name']}")
        print(f"   ID: {agent['id']}")
        print(f"   Category: {agent['compression_category']}")
        print(f"   Length: {agent['char_count']} chars (~{agent['estimated_tokens']} tokens)")
        print(f"   Compression Score: {agent['compression_score']}")
        print(f"   Reasons: {', '.join(agent['compression_reasons'])}")
        print(f"   Preview: {agent['description'][:150]}...")

    # Section 6: Recommendations
    print("\n6. COMPRESSION STRATEGY RECOMMENDATIONS")
    print("-" * 80)

    # Calculate potential savings
    high_chars = sum(a['char_count'] for a in high)
    medium_chars = sum(a['char_count'] for a in medium)

    # Estimate 30% compression for high, 15% for medium
    estimated_high_savings = high_chars * 0.30
    estimated_medium_savings = medium_chars * 0.15
    total_estimated_savings_chars = estimated_high_savings + estimated_medium_savings
    total_estimated_savings_tokens = total_estimated_savings_chars // 4

    print(f"\nPriority 1 - High Compression Potential ({len(high)} agents):")
    print(f"  Current size: {high_chars:,} chars (~{high_chars//4:,} tokens)")
    print(f"  Estimated savings (30% compression): ~{int(estimated_high_savings):,} chars (~{int(estimated_high_savings//4):,} tokens)")
    print("  Techniques:")
    print("    - Remove filler words and redundant phrases")
    print("    - Shorten long sentences (use concise bullet points)")
    print("    - Eliminate verbose constructions ('in order to' → 'to')")
    print("    - Remove excessive punctuation and formatting")

    print(f"\nPriority 2 - Medium Compression Potential ({len(medium)} agents):")
    print(f"  Current size: {medium_chars:,} chars (~{medium_chars//4:,} tokens)")
    print(f"  Estimated savings (15% compression): ~{int(estimated_medium_savings):,} chars (~{int(estimated_medium_savings//4):,} tokens)")
    print("  Techniques:")
    print("    - Tighten sentence structure")
    print("    - Replace verbose phrases with concise alternatives")
    print("    - Preserve essential keywords for discoverability")

    print("\nTotal Estimated Savings:")
    print(f"  Characters: ~{int(total_estimated_savings_chars):,} ({total_estimated_savings_chars/stats['total_chars']*100:.1f}%)")
    print(f"  Tokens: ~{int(total_estimated_savings_tokens):,} ({total_estimated_savings_tokens/stats['total_tokens']*100:.1f}%)")

    print("\n7. ESSENTIAL KEYWORDS TO PRESERVE")
    print("-" * 80)
    print("\nThese keywords appear frequently and are likely important for discoverability:")
    essential_keywords = [kw for kw, count in results['keywords'][:15]]
    print(f"  {', '.join(essential_keywords)}")

    print("\n" + "="*80)
    print("END OF REPORT")
    print("="*80)

def main():
    filepath = '/home/gerald/git/mycelium/plugins/mycelium-core/agents/index.json'
    results = analyze_agents(filepath)
    print_report(results)

    # Save detailed results to JSON for further analysis
    output_file = '/home/gerald/git/mycelium/agent_analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert Counter objects to dicts for JSON serialization
        output_data = {
            'statistics': results['statistics'],
            'longest_10': results['longest'],
            'shortest_10': results['shortest'],
            'top_keywords': dict(results['keywords'][:30]),
            'common_phrases': dict(results['common_phrases'][:20]),
            'compression_summary': {
                'high_count': len(results['compression_categories']['high']),
                'medium_count': len(results['compression_categories']['medium']),
                'low_count': len(results['compression_categories']['low']),
                'high_priority_agents': [
                    {
                        'id': a['id'],
                        'name': a['name'],
                        'chars': a['char_count'],
                        'tokens': a['estimated_tokens'],
                        'score': a['compression_score'],
                        'reasons': a['compression_reasons']
                    }
                    for a in results['compression_categories']['high'][:20]
                ]
            }
        }
        json.dump(output_data, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")

if __name__ == '__main__':
    main()
