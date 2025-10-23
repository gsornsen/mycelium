#!/usr/bin/env python3
"""Detailed Redundancy Analysis for Agent Descriptions
Identifies specific redundant patterns and calculates realistic compression opportunities.
"""

import json
import re
from collections import defaultdict


def analyze_redundancy_patterns(filepath: str):
    """Analyze specific redundancy patterns across agent descriptions."""
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    agents_data = data.get('agents', [])

    # Patterns to analyze
    redundant_patterns = {
        'specializing in': r'\bspecializing in\b',
        'with focus on': r'\bwith focus on\b',
        'focusing on': r'\bfocusing on\b',
        'Masters': r'\bMasters\b',
        'expert': r'\bexpert\b|\bExpert\b',
        'engineer': r'\bengineer\b|\bEngineer\b',
        'developer': r'\bdeveloper\b|\bDeveloper\b',
        'specialist': r'\bspecialist\b|\bSpecialist\b',
        'architect': r'\barchitect\b|\bArchitect\b',
    }

    pattern_usage = defaultdict(list)
    total_chars_by_pattern = defaultdict(int)

    for agent in agents_data:
        desc = agent.get('description', '')
        agent_id = agent.get('id', 'unknown')
        agent_name = agent.get('name', agent_id)

        for pattern_name, pattern_regex in redundant_patterns.items():
            matches = list(re.finditer(pattern_regex, desc))
            if matches:
                pattern_usage[pattern_name].append({
                    'id': agent_id,
                    'name': agent_name,
                    'count': len(matches),
                    'description': desc
                })
                # Count characters in matched phrases
                total_chars_by_pattern[pattern_name] += sum(len(m.group()) for m in matches)

    # Analyze sentence structure patterns
    sentence_patterns = []
    for agent in agents_data:
        desc = agent.get('description', '')
        sentences = [s.strip() for s in re.split(r'[.!?]', desc) if s.strip()]

        for sentence in sentences:
            # Common opening patterns
            if re.match(r'^(Expert|Senior|Specialist|Engineer|Developer|Architect)', sentence):
                sentence_patterns.append({
                    'agent': agent.get('name'),
                    'pattern': 'Role-based opening',
                    'sentence': sentence
                })

    # Print detailed report
    print("="*100)
    print("DETAILED REDUNDANCY ANALYSIS")
    print("="*100)

    print("\n1. REDUNDANT PHRASE ANALYSIS")
    print("-"*100)

    total_redundant_chars = 0

    for pattern_name in sorted(pattern_usage.keys(), key=lambda x: len(pattern_usage[x]), reverse=True):
        count = len(pattern_usage[pattern_name])
        total_chars = total_chars_by_pattern[pattern_name]
        total_redundant_chars += total_chars

        print(f"\nPattern: '{pattern_name}'")
        print(f"  Occurrences: {count} agents")
        print(f"  Total characters: {total_chars}")
        print("  Sample descriptions:")

        for i, usage in enumerate(pattern_usage[pattern_name][:3], 1):
            print(f"    {i}. {usage['name']}: {usage['description'][:80]}...")

    print(f"\nTotal characters in redundant patterns: {total_redundant_chars}")
    print(f"Potential savings by eliminating redundancy: ~{int(total_redundant_chars * 0.5)} chars (~{int(total_redundant_chars * 0.5 / 4)} tokens)")

    # Analyze formulaic structures
    print("\n2. FORMULAIC STRUCTURE ANALYSIS")
    print("-"*100)

    structure_patterns = {
        'Type A: [Role] specializing in [domain]. [Action] [focus]. Masters [skills].': 0,
        'Type B: [Role] expert [action]. [Details] with focus on [aspects].': 0,
        'Type C: [Role] [action]. [Details] focusing on [aspects].': 0,
    }

    type_a_pattern = r'^[A-Z]\w+\s+(expert|engineer|specialist|architect|developer|manager|analyst).*specializing in.*\.\s*\w+.*\.\s*Masters'
    type_b_pattern = r'expert.*\.\s*.*with focus on'
    type_c_pattern = r'\.\s*.*focusing on'

    type_a_count = 0
    type_b_count = 0
    type_c_count = 0

    type_a_examples = []
    type_b_examples = []
    type_c_examples = []

    for agent in agents_data:
        desc = agent.get('description', '')

        if re.search(type_a_pattern, desc):
            type_a_count += 1
            if len(type_a_examples) < 3:
                type_a_examples.append((agent.get('name'), desc))

        if re.search(type_b_pattern, desc):
            type_b_count += 1
            if len(type_b_examples) < 3:
                type_b_examples.append((agent.get('name'), desc))

        if re.search(type_c_pattern, desc):
            type_c_count += 1
            if len(type_c_examples) < 3:
                type_c_examples.append((agent.get('name'), desc))

    print("\nFormulaic Pattern: [Role] specializing in [domain]...")
    print(f"  Count: {type_a_count} agents")
    print("  Examples:")
    for name, desc in type_a_examples:
        print(f"    - {name}: {desc[:90]}...")

    print("\nFormulaic Pattern: ... with focus on [aspects]")
    print(f"  Count: {type_b_count} agents")
    print("  Examples:")
    for name, desc in type_b_examples:
        print(f"    - {name}: {desc[:90]}...")

    print("\nFormulaic Pattern: ... focusing on [aspects]")
    print(f"  Count: {type_c_count} agents")
    print("  Examples:")
    for name, desc in type_c_examples:
        print(f"    - {name}: {desc[:90]}...")

    # Calculate total statistics
    print("\n3. COMPRESSION OPPORTUNITIES")
    print("-"*100)

    total_agents = len(agents_data)
    total_chars = sum(len(agent.get('description', '')) for agent in agents_data)

    compression_strategies = [
        {
            'strategy': 'Replace "specializing in" with "in" or remove entirely',
            'pattern': 'specializing in',
            'occurrences': len(pattern_usage.get('specializing in', [])),
            'chars_saved_per': 13,  # "specializing in" = 14 chars, "in" = 2 chars
            'estimated_savings': len(pattern_usage.get('specializing in', [])) * 12
        },
        {
            'strategy': 'Replace "with focus on" with "focused on" or integrate directly',
            'pattern': 'with focus on',
            'occurrences': len(pattern_usage.get('with focus on', [])),
            'chars_saved_per': 8,  # "with focus on" = 13 chars vs shorter alternatives
            'estimated_savings': len(pattern_usage.get('with focus on', [])) * 8
        },
        {
            'strategy': 'Replace "focusing on" with "focused on" or integrate directly',
            'pattern': 'focusing on',
            'occurrences': len(pattern_usage.get('focusing on', [])),
            'chars_saved_per': 3,
            'estimated_savings': len(pattern_usage.get('focusing on', [])) * 3
        },
        {
            'strategy': 'Remove or simplify "Masters [skills]" sentence (often redundant)',
            'pattern': 'Masters',
            'occurrences': len(pattern_usage.get('Masters', [])),
            'chars_saved_per': 30,  # Assuming average Masters sentence is ~40 chars
            'estimated_savings': len(pattern_usage.get('Masters', [])) * 30
        },
        {
            'strategy': 'Reduce redundant role descriptors (expert/specialist/engineer)',
            'pattern': 'role descriptors',
            'occurrences': 119,  # All agents
            'chars_saved_per': 10,  # Average reduction per description
            'estimated_savings': 119 * 10
        },
    ]

    print("\nRecommended Compression Strategies:")
    print(f"{'Strategy':<70s} {'Occurrences':<15s} {'Est. Savings':<15s}")
    print("-"*100)

    total_estimated_savings = 0
    for strategy in compression_strategies:
        savings = strategy['estimated_savings']
        total_estimated_savings += savings
        print(f"{strategy['strategy']:<70s} {strategy['occurrences']:<15d} ~{savings:>5d} chars")

    print("-"*100)
    print(f"{'Total Estimated Savings:':<70s} {'':15s} ~{total_estimated_savings:>5d} chars")
    print(f"{'Current Total:':<70s} {'':15s} {total_chars:>6d} chars (~{total_chars//4} tokens)")
    print(f"{'After Compression:':<70s} {'':15s} ~{total_chars - total_estimated_savings:>5d} chars (~{(total_chars - total_estimated_savings)//4} tokens)")
    print(f"{'Compression Rate:':<70s} {'':15s} {(total_estimated_savings/total_chars)*100:>5.1f}%")
    print(f"{'Token Savings:':<70s} {'':15s} ~{total_estimated_savings//4:>5d} tokens")

    # Examples of before/after
    print("\n4. BEFORE/AFTER EXAMPLES")
    print("-"*100)

    examples = [
        {
            'before': 'API architecture expert designing scalable, developer-friendly interfaces. Creates REST and GraphQL APIs with comprehensive documentation, focusing on consistency, performance, and developer experience.',
            'after': 'API architecture expert designing scalable interfaces. Creates REST and GraphQL APIs with comprehensive documentation, ensuring consistency, performance, and developer experience.',
            'agent': 'api-designer'
        },
        {
            'before': 'Senior backend engineer specializing in scalable API development and microservices architecture. Builds robust server-side solutions with focus on performance optimization and data integrity.',
            'after': 'Senior backend engineer in scalable API development and microservices. Builds robust server-side solutions ensuring performance optimization and data integrity.',
            'agent': 'backend-developer'
        },
        {
            'before': 'Expert documentation engineer specializing in technical documentation systems, API documentation, and developer-friendly content. Masters documentation-as-code, interactive examples, and versioning strategies.',
            'after': 'Documentation engineer expert in technical documentation systems, API docs, and developer content. Skilled in documentation-as-code, interactive examples, and versioning.',
            'agent': 'documentation-engineer'
        },
    ]

    for i, example in enumerate(examples, 1):
        before_len = len(example['before'])
        after_len = len(example['after'])
        savings = before_len - after_len
        savings_pct = (savings / before_len) * 100

        print(f"\nExample {i}: {example['agent']}")
        print(f"  BEFORE ({before_len} chars): {example['before']}")
        print(f"  AFTER  ({after_len} chars): {example['after']}")
        print(f"  SAVINGS: {savings} chars ({savings_pct:.1f}%) | ~{savings//4} tokens")

    print("\n" + "="*100)

def main():
    filepath = '/home/gerald/git/mycelium/plugins/mycelium-core/agents/index.json'
    analyze_redundancy_patterns(filepath)

if __name__ == '__main__':
    main()
