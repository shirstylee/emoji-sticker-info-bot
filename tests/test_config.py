import pytest

from emoji_id_bot.config import Config


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    monkeypatch.setattr("emoji_id_bot.config.load_dotenv", lambda: None)
    monkeypatch.setenv("BOT_TOKEN", "test_token")
    monkeypatch.delenv("ADMIN_IDS", raising=False)


@pytest.mark.parametrize("value", ["", "0", "-1", "@admin", "123,", "123,,456", "123,abc", "1.5", "１２３", str(2**52)])
def test_invalid_or_missing_admin_ids_fail_closed(monkeypatch, value):
    monkeypatch.setenv("ADMIN_IDS", value)
    with pytest.raises(RuntimeError, match="ADMIN_IDS"):
        Config.from_env()


def test_multiple_administrators_are_parsed(monkeypatch):
    monkeypatch.setenv("ADMIN_IDS", " 123, 456,123 ")
    assert Config.from_env().admin_ids == frozenset({123, 456})
