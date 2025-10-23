#!/usr/bin/env python3
"""Compress verbose agent descriptions in YAML frontmatter to reduce token usage.

Target: 60% reduction per description while maintaining clarity and searchability.
"""

import json
import re
from pathlib import Path


def count_tokens_estimate(text: str) -> int:
    """Estimate token count (rough approximation: ~4 chars per token)."""
    return len(text.split())


def extract_frontmatter(content: str) -> tuple[str, str, str]:
    """Extract YAML frontmatter and body from markdown content."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return "", "", content

    frontmatter = match.group(1)
    body = match.group(2)

    # Extract description
    desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
    description = desc_match.group(1).strip() if desc_match else ""

    return frontmatter, description, body


def compress_description(description: str, agent_name: str) -> str:
    """Compress agent description following established rules:
    1. Remove filler words (Expert, Senior, specializing in, etc.)
    2. Use abbreviations where clear
    3. Use sentence fragments, drop articles
    4. Preserve key information (versions, technologies, distinguishing features)
    """
    # Remove common filler phrases at the beginning
    compressed = description

    # Remove leading expert/senior qualifiers
    compressed = re.sub(r'^(Expert|Senior|Professional|Master)\s+', '', compressed)

    # Remove verbose introductory phrases
    compressed = re.sub(r'\s+specializing in\s+', '. ', compressed)
    compressed = re.sub(r'\s+with (deep|comprehensive|extensive|broad) (expertise|knowledge|experience) in\s+', '. ', compressed)
    compressed = re.sub(r'\s+with (a )?focus on\s+', '. ', compressed)
    compressed = re.sub(r'\s+with emphasis on\s+', '. ', compressed)
    compressed = re.sub(r'\s+focused on\s+', '. ', compressed)

    # Replace "Masters" with nothing or more concise language
    compressed = re.sub(r'\.\s*Masters\s+', '. ', compressed)

    # Remove "while ensuring/maintaining"
    compressed = re.sub(r'\s+while (ensuring|maintaining)\s+', '. ', compressed)

    # Compress "and" lists
    compressed = re.sub(r',\s+and\s+', ', ', compressed)

    # Remove excessive articles where safe
    compressed = re.sub(r'\s+for the\s+', ' for ', compressed)

    # Compress version mentions
    compressed = re.sub(r'modern\s+(\w+\s+\d+)', r'\1', compressed)

    # Simplify "production-ready" to "production"
    compressed = re.sub(r'production-ready\s+', 'production ', compressed)

    # Clean up multiple spaces and periods
    compressed = re.sub(r'\s+', ' ', compressed)
    compressed = re.sub(r'\.\.+', '.', compressed)
    compressed = re.sub(r'\.\s*\.', '.', compressed)

    # Ensure it ends with a period
    compressed = compressed.strip()
    if not compressed.endswith('.'):
        compressed += '.'

    return compressed


def manual_compress_description(description: str, agent_name: str) -> str:
    """Apply manual compression rules for specific agent patterns.
    This provides better compression than automated rules.
    """
    # Create a mapping of common patterns to compress

    # Python-related
    if 'Python 3.13+' in description:
        return "Python 3.13+ specialist. Type-safe async development, data science, web frameworks. Production code quality."

    # Frontend
    if 'frontend' in agent_name.lower() or 'UI engineer' in description:
        return "UI engineer. React, Vue, Angular. Component architecture, state management, performance, accessibility. Production web apps."

    # DevOps
    if 'devops' in agent_name.lower() or 'DevOps engineer' in description:
        return "DevOps automation specialist. CI/CD, containerization, Kubernetes, ArgoCD. Infrastructure as code, monitoring, team collaboration."

    # Backend
    if 'backend' in agent_name.lower() and 'developer' in description:
        return "Backend API specialist. Scalable services, database design, microservices. RESTful/GraphQL APIs, caching, security."

    # Fullstack
    if 'fullstack' in agent_name.lower():
        return "Full-stack developer. Frontend to database expertise. React, Node.js, APIs, deployment. End-to-end feature delivery."

    # Mobile
    if 'mobile' in agent_name.lower() and 'developer' in description:
        return "Mobile app specialist. iOS (Swift), Android (Kotlin), cross-platform. Native performance, responsive UIs, app store deployment."

    # Database
    if 'database' in agent_name.lower() and 'administrator' in description.lower():
        return "Database administration specialist. Performance tuning, backup/recovery, replication, high availability. SQL/NoSQL optimization."

    # Security
    if 'security' in agent_name.lower() and ('engineer' in description or 'auditor' in description):
        return "Security specialist. Vulnerability assessment, penetration testing, secure architecture. OWASP compliance, threat modeling."

    # Testing/QA
    if 'qa-expert' in agent_name or 'test' in agent_name.lower():
        return "Quality assurance specialist. Test automation, CI/CD integration, comprehensive coverage. Bug detection, regression prevention."

    # Multi-agent coordinator
    if 'multi-agent' in agent_name.lower() and 'coordinator' in agent_name.lower():
        return "Multi-agent orchestration specialist. Workflow coordination, parallel execution, fault tolerance. Distributed system communication at scale."

    # Context manager
    if 'context-manager' in agent_name:
        return "Context management specialist. Project state tracking, knowledge graphs, intelligent retrieval. Agent coordination support."

    # Cloud architect
    if 'cloud-architect' in agent_name:
        return "Cloud architecture specialist. AWS, Azure, GCP. Scalable infrastructure, cost optimization, multi-cloud strategies."

    # Kubernetes
    if 'kubernetes' in agent_name.lower():
        return "Kubernetes specialist. Cluster management, service mesh, monitoring. High availability, disaster recovery, GitOps."

    # Fall back to automated compression
    return compress_description(description, agent_name)


def update_frontmatter(frontmatter: str, new_description: str) -> str:
    """Update the description field in frontmatter."""
    return re.sub(
        r'^description:\s*.+$',
        f'description: {new_description}',
        frontmatter,
        flags=re.MULTILINE
    )


def process_agent_file(file_path: Path) -> dict:
    """Process a single agent file and return compression statistics."""
    content = file_path.read_text(encoding='utf-8')

    frontmatter, old_description, body = extract_frontmatter(content)

    if not old_description:
        return {
            'file': file_path.name,
            'status': 'no_description',
            'old_tokens': 0,
            'new_tokens': 0,
            'reduction': 0
        }

    # Try manual compression first, fall back to automated
    new_description = manual_compress_description(old_description, file_path.stem)

    # If manual didn't change it significantly, use automated
    if new_description == old_description or len(new_description) > len(old_description) * 0.7:
        new_description = compress_description(old_description, file_path.stem)

    # Calculate token counts
    old_tokens = count_tokens_estimate(old_description)
    new_tokens = count_tokens_estimate(new_description)
    reduction = ((old_tokens - new_tokens) / old_tokens * 100) if old_tokens > 0 else 0

    # Update frontmatter
    new_frontmatter = update_frontmatter(frontmatter, new_description)

    # Reconstruct file
    new_content = f"---\n{new_frontmatter}\n---\n{body}"

    # Write back to file
    file_path.write_text(new_content, encoding='utf-8')

    return {
        'file': file_path.name,
        'agent_name': file_path.stem,
        'status': 'compressed',
        'old_description': old_description,
        'new_description': new_description,
        'old_tokens': old_tokens,
        'new_tokens': new_tokens,
        'reduction': reduction
    }


def main():
    """Process all agent files and generate compression report."""
    agents_dir = Path('/home/gerald/git/mycelium/plugins/mycelium-core/agents')

    # Find all markdown files except index.json
    agent_files = sorted([f for f in agents_dir.glob('*.md')])

    print(f"Found {len(agent_files)} agent files to process...\n")

    results = []
    for agent_file in agent_files:
        print(f"Processing {agent_file.name}...")
        result = process_agent_file(agent_file)
        results.append(result)

    # Calculate statistics
    successful = [r for r in results if r['status'] == 'compressed']

    if not successful:
        print("\nNo files processed successfully.")
        return

    total_old_tokens = sum(r['old_tokens'] for r in successful)
    total_new_tokens = sum(r['new_tokens'] for r in successful)
    total_saved = total_old_tokens - total_new_tokens
    avg_reduction = sum(r['reduction'] for r in successful) / len(successful)

    print("\n" + "="*80)
    print("COMPRESSION REPORT")
    print("="*80)
    print(f"\nFiles processed: {len(successful)}")
    print(f"Average tokens per description (before): {total_old_tokens / len(successful):.1f}")
    print(f"Average tokens per description (after): {total_new_tokens / len(successful):.1f}")
    print(f"Total tokens saved: {total_saved}")
    print(f"Average compression ratio: {avg_reduction:.1f}%")
    print(f"Target achieved: {'YES' if avg_reduction >= 60 else 'NO (target: 60%)'}")

    # Show best compressions
    print("\n" + "-"*80)
    print("TOP 10 BEST COMPRESSIONS:")
    print("-"*80)
    best = sorted(successful, key=lambda x: x['reduction'], reverse=True)[:10]
    for i, r in enumerate(best, 1):
        print(f"{i}. {r['file']}: {r['reduction']:.1f}% reduction ({r['old_tokens']} → {r['new_tokens']} tokens)")

    # Show examples
    print("\n" + "-"*80)
    print("EXAMPLE TRANSFORMATIONS:")
    print("-"*80)
    for r in best[:3]:
        print(f"\n{r['file']}:")
        print(f"BEFORE ({r['old_tokens']} tokens): {r['old_description']}")
        print(f"AFTER ({r['new_tokens']} tokens): {r['new_description']}")

    # Save detailed report
    report_path = agents_dir / 'compression_report.json'
    with open(report_path, 'w') as f:
        json.dump({
            'summary': {
                'files_processed': len(successful),
                'total_old_tokens': total_old_tokens,
                'total_new_tokens': total_new_tokens,
                'total_saved': total_saved,
                'average_reduction': avg_reduction,
                'target_met': avg_reduction >= 60
            },
            'results': results
        }, f, indent=2)

    print(f"\n\nDetailed report saved to: {report_path}")
    print("\nNext step: Run 'python scripts/generate_agent_index.py' to update index.json")


if __name__ == '__main__':
    main()
