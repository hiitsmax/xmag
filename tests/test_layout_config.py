import pytest
from pydantic import ValidationError

from xmag.config import ImageLayoutMode, LayoutConfig, PaginationMode, PaperSize


def test_layout_config_defaults() -> None:
    config = LayoutConfig()
    assert config.paper == PaperSize.A4
    assert config.columns == 3
    assert config.outer_margin_mm == 4.0
    assert config.inner_margin_mm == 9.0
    assert config.pagination == PaginationMode.CONTINUOUS
    assert config.image_layout == ImageLayoutMode.SPAN


def test_layout_config_requires_inner_margin_larger_than_outer() -> None:
    with pytest.raises(ValidationError):
        LayoutConfig(inner_margin_mm=2.0, outer_margin_mm=4.0)


def test_layout_config_requires_positive_gap() -> None:
    with pytest.raises(ValidationError):
        LayoutConfig(column_gap_mm=0)
