import subprocess
from pathlib import Path

from scripts.check_publication import scan


def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def fake_token() -> str:
    # Deliberately assembled at runtime so the test source contains no token.
    return "123456789:" + "a" * 35


def test_staged_secret_is_found_even_if_worktree_was_cleaned(tmp_path: Path) -> None:
    root = repo(tmp_path)
    source = root / "config.py"
    source.write_text(fake_token(), encoding="utf-8")
    run_git(root, "add", "config.py")
    source.write_text("load_token_from_env()", encoding="utf-8")
    findings, _ = scan(root)
    assert any("index: config.py" in item and "Telegram bot token" in item for item in findings)
    assert all(fake_token() not in item for item in findings)


def test_deleted_secret_is_found_in_history(tmp_path: Path) -> None:
    root = repo(tmp_path)
    source = root / ".env"
    source.write_text(fake_token(), encoding="utf-8")
    run_git(root, "add", ".env")
    run_git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "-qm", "Add configuration")
    run_git(root, "rm", ".env")
    run_git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "-qm", "Remove configuration")
    findings, _ = scan(root, history=True)
    assert any("history" in item and "Telegram bot token" in item for item in findings)
    assert any("history" in item and "private/runtime file" in item for item in findings)
    assert all(fake_token() not in item for item in findings)


def test_ignored_local_data_and_public_example_are_safe(tmp_path: Path) -> None:
    root = repo(tmp_path)
    (root / ".gitignore").write_text(".env\ndata/\n", encoding="utf-8")
    (root / ".env").write_text(fake_token(), encoding="utf-8")
    (root / "data").mkdir()
    (root / "data" / "bot.db").write_bytes(b"private user settings")
    (root / ".env.example").write_text("BOT_TOKEN=1234567890:replace_me", encoding="utf-8")
    (root / "ids.txt").write_text("6028346797368283073", encoding="utf-8")
    assert scan(root)[0] == []


def test_untracked_database_copy_is_flagged(tmp_path: Path) -> None:
    root = repo(tmp_path)
    (root / "backup.sqlite3").write_bytes(b"private")
    assert any("backup.sqlite3" in item for item in scan(root)[0])
