from typing import Callable, TypedDict, List, Mapping, Any, Tuple


class Page(TypedDict):
    start: Tuple[int, int]
    lines: int


class PageStyle:
    text_size = 24
    header_size = [
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
    justify = 'left'
    margin: Tuple[int, int, int, int] = (10, 10, 10, 10)
    columns: int = 1
    lines: int = 60
    color = (20, 20, 10)

    _line_width: int

    def __init__(self, d: Mapping[str, Any] = {}):
        self.__dict__.update(**d)

    def calculate_line_width(self, text_renderer: Callable[[str], Tuple[int, int]]) -> int:
        self._line_width = text_renderer(
            "A" * self.linelength)[0]

        return self._line_width
