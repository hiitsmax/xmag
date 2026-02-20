import shutil
from datetime import datetime, timezone

import pytest

from xmag.compiler import compile_tex_with_tectonic
from xmag.config import LayoutConfig
from xmag.models import ArticleContent
from xmag.renderer import render_issue_tex


def test_compile_smoke(tmp_path) -> None:
    if shutil.which("tectonic") is None:
        pytest.skip("tectonic not available")

    article = ArticleContent(
        status_id="111",
        url="https://x.com/alice/status/111",
        author_name="Alice",
        author_handle="@alice",
        published_at=datetime(2026, 2, 20, 12, 0, tzinfo=timezone.utc),
        text="Hello world from test article.",
        media_urls=[],
    )

    tex = render_issue_tex([article], {"111": []}, LayoutConfig())
    tex_path = tmp_path / "issue.tex"
    tex_path.write_text(tex, encoding="utf-8")

    output = tmp_path / "issue.pdf"
    compile_tex_with_tectonic(tex_path, output)

    assert output.exists()
    assert output.stat().st_size > 0
