import json

from emoji_id_bot.db import SETTING_COLUMNS
from emoji_id_bot.exports import settings_json
from emoji_id_bot.models import ResultSettings


def test_settings_export_contains_only_shared_configuration():
    settings = ResultSettings(display_mode="both", id_style="code", deduplicate=True,
                              language="en", is_admin=True, settings_scope="personal", spaces_around_dash=False)
    payload = json.loads(settings_json(settings))
    assert payload["schema_version"] == 1
    assert set(payload) == {"schema_version", "settings"}
    assert set(payload["settings"]) == SETTING_COLUMNS
    assert payload["settings"]["display_mode"] == "both"
    assert payload["settings"]["deduplicate"] is True
    assert payload["settings"]["spaces_around_dash"] is False
    assert "language" not in payload["settings"]
    assert "is_admin" not in payload["settings"]
    assert "settings_scope" not in payload["settings"]
    restored = ResultSettings(**payload["settings"])
    assert settings_json(restored) == settings_json(settings)
