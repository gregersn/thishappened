from enum import Enum
import logging
from optparse import Option
from pathlib import Path
from typing import Callable, List, Literal, Optional, TypedDict, Mapping, Any, Tuple

logger = logging.getLogger("pagestyle")


class Margin(Enum):
    top = 0
    right = 1
    bottom = 2
    left = 3


class Page(TypedDict):
    start: Tuple[int, int]
    lines: int


TextRenderer = Callable[[str], Tuple[int, int]]


class PageStyle:
    """Page properites."""
    _font_size: int = 24
    _header_font_size: List[int] = [
        40,
        38,
        36,
        34,
        32,
    ]
    background: Optional[Path] = None
    font: Path = Path("/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf")
    font_bold: Path = Path(
        "/usr/share/fonts/truetype/ttf-bitstream-vera/VeraBd.ttf")
    font_italic: Path = Path(
        "/usr/share/fonts/truetype/ttf-bitstream-vera/VeraIt.ttf")
    linelength: int = 80
    linespacing: int = 0
    column_spacing: int = 32
    variation: Tuple[float, float] = (0.0, 0.0)
    justify: Literal['Left', 'Right', 'Center', 'Block'] = 'Left'
    margin: Tuple[int, int, int,
                  int] = (10, 10, 10, 10)  # Top, right, bottom, left
    columns: int = 1
    lines: int = 60
    color: Tuple[int, int, int] = (20, 20, 10)
    outputsize: Tuple[int, int] = (800, 1200)
    paragraph: Optional[Literal['Indent', 'Newline']] = 'Newline'

    _line_width: int

    _font_size_multiplier: float = 1.0

    def __init__(self, d: Mapping[str, Any] = {}):
        self.__dict__.update(**d)

    def size_fit(self, text_renderer: TextRenderer):
        """Adjust the font size _down_ to the usable canvas size."""

        # Number of pixels needed to place a given number of characters after each other.
        linesize = text_renderer("a" * self.linelength)

        # The amount of pixels that can be used, width wise, to add text to.
        usable_line_width = (
            self.outputsize[0] - self.margin[Margin.left.value] -
            self.margin[Margin.right.value] -
            (self.columns - 1) * self.column_spacing) // self.columns

        logger.debug(
            f"Current linesize is {linesize[0]}, and usable canvas is  {usable_line_width}"
        )

        if linesize[0] > usable_line_width:
            self._font_size_multiplier = usable_line_width / linesize[0]

    def calculate_line_width(self, text_renderer: TextRenderer) -> int:
        self._line_width = text_renderer("a" * self.linelength)[0]
        logger.debug(
            "Line width in pixels was calculated to %s with text length %s",
            self._line_width, self.linelength)

        return self._line_width

    @property
    def text_size(self):
        return int(self._font_size * self._font_size_multiplier)

    @property
    def header_size(self):
        return [
            int(hs * self._font_size_multiplier)
            for hs in self._header_font_size
        ]

    def get_font(self, variant: Literal["", "bold", "italic"] = "") -> Path:
        """Return the current font."""
        if variant == 'bold':
            f = Path(self.font_bold)
        elif variant == 'italic':
            f = Path(self.font_italic)
        else:
            f = Path(self.font)

        if not f.exists():
            # If the font does not exist local to the document/settings, check the central assets folder.
            f = Path(__file__).parent.parent.parent / "assets" / f

            if not f.exists():
                raise FileNotFoundError(f"Could not find fontfile {f}.")

        return f
