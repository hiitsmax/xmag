from xmag.renderer import latex_escape


def test_latex_escape_special_characters() -> None:
    text = r"50% of #1_cost is $5 & tax_{x} with \\slash and {braces}~^"
    escaped = latex_escape(text)

    assert r"\%" in escaped
    assert r"\#" in escaped
    assert r"\_" in escaped
    assert r"\$" in escaped
    assert r"\&" in escaped
    assert r"\{" in escaped
    assert r"\}" in escaped
    assert r"\textbackslash{}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped
