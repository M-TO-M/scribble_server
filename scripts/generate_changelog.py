import re
import sys
import argparse
import subprocess
from pathlib import Path


def get_tag():
    gh_cli = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    p = subprocess.run(gh_cli, capture_output=True)
    tag = p.stdout.decode().strip()
    return tag


def get_prev_tag():
    gh_cli = ['git', 'rev-list', '--abbrev-commit', '--tags', '--skip=1', '--max-count=1']
    rev = subprocess.run(gh_cli, capture_output=True).stdout.decode().strip()

    tag_gh_cli = ['git', 'describe', '--abbrev=0', '--tags', f'{rev}']
    p = subprocess.run(tag_gh_cli, capture_output=True)
    tag = p.stdout.decode().strip()
    return tag


def get_repo_url():
    p = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True)
    url = p.stdout.decode().strip()
    return url


def get_change_log_content(prev_tag, tag):
    p = subprocess.run(['git', 'log', '--oneline', '--format=" * %s"', f'{prev_tag}..{tag}'], capture_output=True)
    content = p.stdout.decode().strip("\"")
    return content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', '-v', type=str, default=False,
        help="Declare the newest release version in 'YY.MM.*' format."
    )
    args = parser.parse_args()
    if not args.version:
        print("::error ::No version given from args.")
        sys.exit(1)

    repo_url = get_repo_url()
    m = re.match(r'^(https://)[a-zA-Z0-9-]+\.(com)+/[a-zA-Z-_.]+/[a-zA-Z-_]+', repo_url, re.S)

    prev_tag, tag = get_prev_tag(), get_tag()
    commit_log_url = f"{m.group().strip()}/compare/{prev_tag}...{tag}"

    try:
        input_path = Path('./CHANGELOG.md')
        input_path.touch(exist_ok=True)
        input_text = input_path.read_text().strip()

        output_path = Path('./CHANGELOG_RELEASE.md')
        output_text = (
            "## %s\n-------------\n### Features\n%s\n"
            "### Full Commit Logs\nCheck out [the full commit logs](%s) until this release (%s).\n\n"
            % (args.version, get_change_log_content(prev_tag, tag), commit_log_url, args.version)
        )
        input_path.write_text(output_text + "\n\n" + input_text)
        output_path.write_text(output_text)
    except IOError as e:
        sys.exit(1)


if __name__ == '__main__':
    main()
