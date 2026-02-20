"""Configuration models and enums for xmag."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PaperSize(str, Enum):
    A4 = "a4"
    LETTER = "letter"


class PaginationMode(str, Enum):
    CONTINUOUS = "continuous"
    NEWPAGE = "newpage"
    SPLIT = "split"


class ImageLayoutMode(str, Enum):
    SPAN = "span"
    INLINE = "inline"
    APPENDIX = "appendix"


class LayoutConfig(BaseModel):
    """User-adjustable layout settings for the generated LaTeX PDF."""

    paper: PaperSize = PaperSize.A4
    columns: int = Field(default=3, ge=1, le=6)
    outer_margin_mm: float = Field(default=4.0, gt=0)
    inner_margin_mm: float = Field(default=9.0, gt=0)
    top_margin_mm: float = Field(default=10.0, gt=0)
    bottom_margin_mm: float = Field(default=10.0, gt=0)
    column_gap_mm: float = Field(default=4.0, gt=0)
    pagination: PaginationMode = PaginationMode.NEWPAGE
    image_layout: ImageLayoutMode = ImageLayoutMode.INLINE
    blank_first_page: bool = False
    include_index_page: bool = False

    @model_validator(mode="after")
    def validate_margin_relationship(self) -> "LayoutConfig":
        if self.inner_margin_mm < self.outer_margin_mm:
            raise ValueError("inner_margin_mm should be >= outer_margin_mm for two-sided layout")
        return self
