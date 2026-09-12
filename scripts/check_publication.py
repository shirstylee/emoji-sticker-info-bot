"""Check publishable files, the Git index and optional history without printing secrets.

Uses only Python's standard library and Git. This is a focused check, not a
guarantee that every possible credential or personal detail will be detected.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path, PurePosixPath


MAX_FILE_BYTES = 8 * 1024 * 1024
SECRET_PATTERNS = {
    "Telegram bot token": rb"(?<![A-Za-z0-9_])[0-9]{6,12}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])",
    "GitHub token": rb"\b(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,})\b",
    "private key": rb"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----",
    "AWS access key": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
}
PRIVATE_DIRS = {
    ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    "data", "backups", "exports", "logs",
}
PRIVATE_SUFFIX = re.compile(
    r"(?:\.db|\.sqlite3?)(?:-.*)?$|\.(?:log|bak|pem|key|p12|pfx|pyc)$",
    re.IGNORECASE,
)


def private_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    name = parts[-1].lower()
    return (
        any(part.lower() in PRIVATE_DIRS or part.endswith(".egg-info") for part in parts)
        or (name.startswith(".env") and name != ".env.example")
        or PRIVATE_SUFFIX.search(name) is not None
    )


def secret_kinds(content: bytes) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if re.search(pattern, content)]


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        # Git errors can include paths or URLs; do not echo arbitrary stderr.
        raise RuntimeError(f"Git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def scan(root: Path, *, history: bool = False) -> tuple[list[str], int]:
    findings: set[str] = set()
    checked = 0
    seen_blobs: set[str] = set()

    def inspect(content: bytes, label: str) -> None:
        nonlocal checked
        checked += 1
        for kind in secret_kinds(content):
            findings.add(f"{label}: possible {kind} (value hidden)")

    def inspect_blob(oid: str, path: str, location: str) -> None:
        label = f"{location}: {path}"
        if private_path(path):
            findings.add(f"{label}: private/runtime file")
        if oid in seen_blobs:
            return
        seen_blobs.add(oid)
        size = int(git(root, "cat-file", "-s", oid))
        if size > MAX_FILE_BYTES:
            findings.add(f"{label}: exceeds 8 MiB; manual review required")
            return
        inspect(git(root, "cat-file", "blob", oid), label)

    paths = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    for raw_path in sorted(set(paths.split(b"\0")) - {b""}):
        path = raw_path.decode("utf-8")
        candidate = root / path
        if not candidate.exists():
            continue
        if private_path(path):
            findings.add(f"worktree: {path}: private/runtime file")
        if candidate.is_symlink() or not candidate.is_file():
            findings.add(f"worktree: {path}: link or non-file requires manual review")
            continue
        if candidate.stat().st_size > MAX_FILE_BYTES:
            findings.add(f"worktree: {path}: exceeds 8 MiB; manual review required")
            continue
        inspect(candidate.read_bytes(), f"worktree: {path}")

    # A staged secret must still be caught after the working file has been cleaned.
    index = git(root, "ls-files", "--stage", "-z")
    for record in filter(None, index.split(b"\0")):
        metadata, path = record.split(b"\t", 1)
        mode, oid, _ = metadata.decode().split()
        if mode == "160000":
            findings.add(f"index: {path.decode('utf-8')}: submodule requires manual review")
            continue
        inspect_blob(oid, path.decode("utf-8"), "index")

    if history:
        if git(root, "rev-parse", "--is-shallow-repository").strip() == b"true":
            findings.add("history: shallow clone; complete history is required")
        for commit in git(root, "rev-list", "--all").decode().splitlines():
            inspect(git(root, "show", "-s", "--format=%B", commit), f"commit {commit[:12]}")
            tree = git(root, "ls-tree", "-r", "-z", "--full-tree", commit)
            for record in filter(None, tree.split(b"\0")):
                metadata, path = record.split(b"\t", 1)
                _, kind, oid = metadata.decode().split()
                if kind == "blob":
                    inspect_blob(oid, path.decode("utf-8"), f"history {commit[:12]}")
                else:
                    findings.add(f"history {commit[:12]}: submodule requires manual review")
    return sorted(findings), checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true", help="also scan all local Git refs")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository directory")
    args = parser.parse_args()
    try:
        root = Path(git(args.root, "rev-parse", "--show-toplevel").decode().strip())
        findings, checked = scan(root, history=args.history)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Publication check could not finish: {type(error).__name__}")
        return 2
    for finding in findings:
        print(f"FAIL: {finding}")
    if findings:
        print(f"Review required: {len(findings)} finding(s). Secret values were not printed.")
        return 1
    scope = "worktree, index and local Git history" if args.history else "worktree and index"
    print(f"OK: {scope}; {checked} content checks; no matching secrets or private files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
