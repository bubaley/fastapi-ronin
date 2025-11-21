#!/usr/bin/env python3
"""
Documentation testing script for FastAPI Ronin.

This script performs various checks on the documentation to ensure quality and consistency.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, '', f'Command not found: {cmd[0]}'


def check_mkdocs_build() -> bool:
    """Check if MkDocs can build successfully."""
    print('🔨 Testing MkDocs build...')

    exit_code, stdout, stderr = run_command(['uv', 'run', 'mkdocs', 'build', '--clean', '--strict'])

    if exit_code == 0:
        print('✅ MkDocs build successful')
        return True
    else:
        print('❌ MkDocs build failed')
        print(f'Error: {stderr}')
        return False


def check_internal_links() -> bool:
    """Check for broken internal links in documentation."""
    print('🔗 Checking internal links...')

    docs_dir = Path('docs')
    broken_links = []

    for md_file in docs_dir.rglob('*.md'):
        with open(md_file, encoding='utf-8') as f:
            content = f.read()

        # Find markdown links
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for link_text, link_url in md_links:
            # Skip external links and anchors
            if link_url.startswith(('http', '#')):
                continue

            # Check if internal .md file exists
            if link_url.endswith('.md'):
                # Handle relative paths correctly
                current_dir = md_file.parent
                target_path = current_dir / link_url
                if not target_path.exists():
                    # Try relative to docs root as fallback
                    target_path_alt = docs_dir / link_url
                    if not target_path_alt.exists():
                        broken_links.append(f'{md_file.relative_to(docs_dir)}: {link_url}')

    if broken_links:
        print('❌ Broken internal links found:')
        for link in broken_links:
            print(f'  - {link}')
        return False
    else:
        print('✅ No broken internal links found')
        return True


def check_empty_links() -> bool:
    """Check for empty links in documentation."""
    print('🔍 Checking for empty links...')

    docs_dir = Path('docs')
    empty_links = []

    for md_file in docs_dir.rglob('*.md'):
        with open(md_file, encoding='utf-8') as f:
            content = f.read()

        # Find empty links [text]()
        if ']()' in content:
            empty_links.append(str(md_file.relative_to(docs_dir)))

    if empty_links:
        print('❌ Empty links found in:')
        for file in empty_links:
            print(f'  - {file}')
        return False
    else:
        print('✅ No empty links found')
        return True


def check_spelling() -> bool:
    """Basic spell checking for common typos."""
    print('📝 Checking for common typos...')

    docs_dir = Path('docs')
    typos = [
        'teh',
        'adn',
        'nad',
        'hte',
        'documetnation',
        'implmentation',
        'configuraiton',
        'reponse',
        'requst',
        'paramter',
    ]

    found_typos = []

    for md_file in docs_dir.rglob('*.md'):
        with open(md_file, encoding='utf-8') as f:
            content = f.read().lower()

        for typo in typos:
            if typo in content:
                found_typos.append(f'{md_file.relative_to(docs_dir)}: {typo}')

    if found_typos:
        print('❌ Potential typos found:')
        for typo in found_typos[:10]:  # Limit output
            print(f'  - {typo}')
        if len(found_typos) > 10:
            print(f'  ... and {len(found_typos) - 10} more')
        return False
    else:
        print('✅ No common typos found')
        return True


def check_code_examples() -> bool:
    """Check if code examples are properly formatted."""
    print('💻 Checking code examples...')

    docs_dir = Path('docs')
    issues = []

    for md_file in docs_dir.rglob('*.md'):
        with open(md_file, encoding='utf-8') as f:
            lines = f.readlines()

        in_code_block = False
        code_lang = None

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting code block
                    in_code_block = True
                    code_lang = line.strip()[3:].strip()

                    # Check if Python code blocks have language specified
                    if not code_lang and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if any(keyword in next_line for keyword in ['from ', 'import ', 'def ', 'class ', 'async ']):
                            issues.append(
                                f'{md_file.relative_to(docs_dir)}:{i + 1}: Python code block without language'
                            )
                else:
                    # Ending code block
                    in_code_block = False
                    code_lang = None

    if issues:
        print('❌ Code formatting issues found:')
        for issue in issues[:5]:  # Limit output
            print(f'  - {issue}')
        if len(issues) > 5:
            print(f'  ... and {len(issues) - 5} more')
        return False
    else:
        print('✅ Code examples look good')
        return True


def main():
    """Run all documentation checks."""
    print('🚀 Starting documentation tests for FastAPI Ronin\n')

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    checks = [
        ('MkDocs Build', check_mkdocs_build),
        ('Internal Links', check_internal_links),
        ('Empty Links', check_empty_links),
        ('Spelling', check_spelling),
        ('Code Examples', check_code_examples),
    ]

    results = []

    for check_name, check_func in checks:
        print(f'\n{"=" * 50}')
        print(f'Running: {check_name}')
        print('=' * 50)

        success = check_func()
        results.append((check_name, success))

    print(f'\n{"=" * 50}')
    print('RESULTS SUMMARY')
    print('=' * 50)

    all_passed = True
    for check_name, success in results:
        status = '✅ PASS' if success else '❌ FAIL'
        print(f'{check_name:20} {status}')
        if not success:
            all_passed = False

    print(f'\n{"=" * 50}')
    if all_passed:
        print('🎉 All documentation checks passed!')
        sys.exit(0)
    else:
        print('💥 Some documentation checks failed!')
        sys.exit(1)


if __name__ == '__main__':
    main()
