#!/usr/bin/env python3
"""Create a verified/signed commit from staged changes using the GitHub Commits API.

Usage:
    git add <files>
    gh-app-commit.py --token ghs_xxx -m "commit message"

The script reads staged changes from the local index, uploads them via the
GitHub API authenticated with a GitHub App installation token, and updates
the current branch ref. The resulting commit shows as "Verified" on GitHub.
"""

import argparse
import base64
import json
import subprocess
import sys
import urllib.request
import urllib.error


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_repo_info():
    remote_url = run(["git", "remote", "get-url", "origin"])
    # Handle SSH (git@github.com:owner/repo.git) and HTTPS (https://github.com/owner/repo.git)
    if remote_url.startswith("git@"):
        path = remote_url.split(":", 1)[1]
    else:
        path = "/".join(remote_url.split("/")[-2:])
    path = path.removesuffix(".git")
    owner, repo = path.split("/", 1)
    return owner, repo


def get_current_branch():
    return run(["git", "symbolic-ref", "--short", "HEAD"])


def get_staged_files():
    """Return list of (status, path) for staged changes."""
    output = run(["git", "diff", "--cached", "--name-status"])
    if not output:
        return []
    files = []
    for line in output.splitlines():
        parts = line.split("\t", 1)
        status, path = parts[0][0], parts[1]  # First char handles R100 etc.
        files.append((status, path))
    return files


def repo_api(token, owner, repo, method, path, data=None):
    url = f"https://api.github.com/repos/{owner}/{repo}{path}"
    payload = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        method=method,
        data=payload,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"GitHub API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create a signed commit via the GitHub Commits API.")
    parser.add_argument("--token", required=True, help="GitHub App installation token (ghs_...)")
    parser.add_argument("-m", "--message", required=True, help="Commit message")
    parser.add_argument("--branch", help="Target branch (default: current branch)")
    args = parser.parse_args()

    # Verify we're in a git repo
    run(["git", "rev-parse", "--is-inside-work-tree"])

    owner, repo = get_repo_info()
    branch = args.branch or get_current_branch()
    token = args.token
    print(f"Repo: {owner}/{repo}, branch: {branch}")

    # Get staged changes
    staged = get_staged_files()
    if not staged:
        print("Nothing staged. Use 'git add' first.", file=sys.stderr)
        sys.exit(1)

    print(f"Staged changes ({len(staged)} files):")
    for status, path in staged:
        print(f"  {status}\t{path}")

    # Get the branch HEAD
    ref_data = repo_api(token, owner, repo, "GET", f"/git/ref/heads/{branch}")
    base_sha = ref_data["object"]["sha"]
    commit_data = repo_api(token, owner, repo, "GET", f"/git/commits/{base_sha}")
    base_tree_sha = commit_data["tree"]["sha"]
    print(f"Base commit: {base_sha[:12]}")

    # Build tree entries from staged files
    tree_entries = []
    for status, path in staged:
        if status == "D":
            # Deleted files: omit from tree by setting sha to null
            tree_entries.append({
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": None,
            })
        else:
            # Added or modified: read content from the index (staged version)
            content = subprocess.run(
                ["git", "show", f":{path}"],
                capture_output=True,
            ).stdout

            blob = repo_api(token, owner, repo, "POST", "/git/blobs", {
                "content": base64.b64encode(content).decode(),
                "encoding": "base64",
            })
            # Preserve the file mode from the index
            mode_output = run(["git", "ls-files", "-s", path])
            mode = mode_output.split(" ", 1)[0]
            tree_entries.append({
                "path": path,
                "mode": mode,
                "type": "blob",
                "sha": blob["sha"],
            })
            print(f"  Uploaded: {path}")

    # Create tree
    new_tree = repo_api(token, owner, repo, "POST", "/git/trees", {
        "base_tree": base_tree_sha,
        "tree": tree_entries,
    })
    print(f"Tree: {new_tree['sha'][:12]}")

    # Create commit
    new_commit = repo_api(token, owner, repo, "POST", "/git/commits", {
        "message": args.message,
        "tree": new_tree["sha"],
        "parents": [base_sha],
    })
    sha = new_commit["sha"]
    verified = new_commit.get("verification", {}).get("verified", False)
    reason = new_commit.get("verification", {}).get("reason", "unknown")
    print(f"Commit: {sha[:12]} (verified={verified}, reason={reason})")

    # Update branch ref
    repo_api(token, owner, repo, "PATCH", f"/git/refs/heads/{branch}", {
        "sha": sha,
    })
    print(f"Branch {branch} updated.")

    # Reset the local staged changes and pull the new commit
    print("Syncing local branch...")
    subprocess.run(["git", "fetch", "origin", branch], capture_output=True)
    subprocess.run(["git", "reset", "--hard", f"origin/{branch}"], capture_output=True)

    print(f"\nhttps://github.com/{owner}/{repo}/commit/{sha}")


if __name__ == "__main__":
    main()
