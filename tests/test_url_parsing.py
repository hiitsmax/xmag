from pathlib import Path

import pytest

from xmag.input import load_url_file, parse_status_id


def test_parse_status_id_accepts_x_and_twitter_hosts() -> None:
    assert parse_status_id("https://x.com/alice/status/12345") == "12345"
    assert parse_status_id("https://twitter.com/bob/status/9999?s=20") == "9999"
    assert parse_status_id("https://www.x.com/user/status/100") == "100"


def test_parse_status_id_rejects_invalid_url() -> None:
    with pytest.raises(ValueError):
        parse_status_id("https://example.com/alice/status/12345")

    with pytest.raises(ValueError):
        parse_status_id("https://x.com/alice/post/12345")


def test_load_url_file_deduplicates_and_skips_comments(tmp_path: Path) -> None:
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "\n".join(
            [
                "# comment",
                "https://x.com/a/status/111",
                "https://x.com/a/status/111",
                "https://twitter.com/b/status/222",
                "",
            ]
        ),
        encoding="utf-8",
    )

    items = load_url_file(url_file)
    assert [item.status_id for item in items] == ["111", "222"]


def test_load_url_file_reports_line_number_on_invalid(tmp_path: Path) -> None:
    url_file = tmp_path / "urls.txt"
    url_file.write_text("https://x.com/a/status/111\nhttps://x.com/a/invalid\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        load_url_file(url_file)
