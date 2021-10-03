from enum import Enum
import logging
from typing import Callable, Text, TypedDict, List, Mapping, Any, Tuple


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
    _text_size = 24
    _header_size = [
        40,
        38,
        36,
        34,
        32, ]
    background = None
    font = "/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf"
    font_bold = "/usr/share/fonts/truetype/ttf-bitstream-vera/VeraBd.ttf"
    font_italic = "/usr/share/fonts/truetype/ttf-bitstream-vera/VeraIt.ttf"
    linelength = 20
    linespacing = 0
    column_spacing = 32
    variation: Tuple[float, float] = (0.0, 0.0)
    justify = 'Left'
    margin: Tuple[int, int, int, int] = (
        10, 10, 10, 10)  # Top, right, bottom, left
    columns: int = 1
    lines: int = 60
    color = (20, 20, 10)
    outputsize = (800, 1200)

    _line_width: int

    _text_size_multiplier: float = 1.0

    def __init__(self, d: Mapping[str, Any] = {}):
        self.__dict__.update(**d)

    def size_fit(self, text_renderer: TextRenderer):
        linesize = text_renderer("A" * self.linelength)
        usable_line_width = self.outputsize[0] - \
            self.margin[Margin.left.value] - self.margin[Margin.right.value]

        logger.debug(
            f"Current linesize is {linesize[0]}, and usable canvas is  {usable_line_width}")

        if linesize[0] > usable_line_width:
            self._text_size_multiplier = usable_line_width / linesize[0]

    def calculate_line_width(self, text_renderer: TextRenderer) -> int:
        self._line_width = text_renderer(
            "A" * self.linelength)[0]

        return self._line_width

    @property
    def text_size(self):
        return int(self._text_size * self._text_size_multiplier)

    @property
    def header_size(self):
        return [int(hs * self._text_size_multiplier) for hs in self._header_size]
