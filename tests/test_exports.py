from emoji_id_bot.exports import ExportStore, html_lines_to_text, safe_export_filename


def test_export_is_bound_to_its_owner() -> None:
    store = ExportStore()
    token = store.put(42, "ids.txt", "one\n")
    assert store.get(token, 7) is None
    assert store.get(token, 42).content == "one\n"


def test_expired_export_is_removed() -> None:
    store = ExportStore(ttl_seconds=0)
    token = store.put(42, "ids.txt", "one\n")
    assert store.get(token, 42) is None


def test_html_result_becomes_readable_txt() -> None:
    content = html_lines_to_text(
        [
            '<tg-emoji emoji-id="123">📁</tg-emoji> <b>Pack</b>',
            '<a href="https://t.me/addemoji/Test">Открыть пак</a>',
            '1) ✈️ [<code>123</code>]',
        ]
    )
    assert content == (
        "📁 Pack\nОткрыть пак: https://t.me/addemoji/Test\n1) ✈️ [123]\n"
    )


def test_txt_export_removes_anti_card_zero_width_separator() -> None:
    content = html_lines_to_text(["545625689&#8203;1548081456"])
    assert content == "5456256891548081456\n"


def test_export_filename_is_safe() -> None:
    assert safe_export_filename("Pack name/ids") == "Pack_name_ids.txt"
