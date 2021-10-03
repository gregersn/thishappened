from typing import Literal, NoReturn, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageChops, ImageFilter
from PIL.ImageFont import FreeTypeFont
from enum import Enum, auto

from logging import getLogger

logger = getLogger(__name__)


class Justify(Enum):
    Left = auto()
    Right = auto()
    Center = auto()
    Block = auto()


class Canvas:
    _page: Image.Image
    _background: Image.Image
    _ctx: ImageDraw.ImageDraw
    fill: Tuple[int, int, int]

    def __init__(self, size: Tuple[int, int]):
        self._size = size
        self.fill = (0, 0, 0)

    def font(self, font: FreeTypeFont):
        self._font = font

    def pagebreak(self) -> NoReturn:
        raise NotImplementedError

    def start_page(self):
        self._page = self._background.copy()
        self._ctx = ImageDraw.ImageDraw(self._page)

    def end_page(self):
        pass

    def background(self, img: Image.Image):
        self._background = img.copy()

    def get(self) -> Image.Image:
        return self._page
        # out = self.compose(self._current_page, outputsize=self._outputsize)

    def text(self,
             data: str,
             position: Tuple[int, int],
             linewidth: int,
             justify: Justify = Justify.Left,
             max_spacing: float = 1.6, variation: Tuple[float, float] = (0.0, 0.0)):
        if not data:
            return position
        text_size: Tuple[int, int] = self._font.getsize(data)

        logger.debug(
            f"Adding text of size {text_size} to line of size {linewidth}")

        if justify == Justify.Block:
            spacer = linewidth / text_size[0]
            if spacer > 1.0:
                for c in data:
                    self._ctx.text(
                        position, c, font=self._font, fill=self.fill)
                    position = (position[0] + self._font.getsize(c)
                                [0] * min(spacer, max_spacing), position[1])
            else:
                self._ctx.text(position, data, font=self._font, fill=self.fill)
                position = (position[0] + text_size[0], position[1])
        elif justify == Justify.Right:
            self._ctx.text((position[0] + linewidth - text_size[0],
                           position[1]), data, font=self._font, fill=self.fill)
            position = (position[0] + text_size[0], position[1])

        elif justify == Justify.Center:
            self._ctx.text((position[0] + (linewidth - text_size[0]) // 2,
                           position[1]), data, font=self._font, fill=self.fill)
            position = (position[0] + text_size[0], position[1])
        else:
            self._ctx.text(position, data, font=self._font, fill=self.fill)
            position = (position[0] + text_size[0], position[1])

        return position

    def compose(self, overlay: Image.Image, outputsize: Optional[Tuple[int, int]] = None) -> Image.Image:
        out = self.background_image.copy()
        text_layer = ImageChops.overlay(
            overlay, self.background_image.copy().convert('RGB'))
        mask_layer = text_layer.copy()
        mask_layer = mask_layer.convert('L')
        mask_layer = ImageChops.invert(mask_layer)
        mask_layer = mask_layer.filter(ImageFilter.GaussianBlur(0))

        out.paste(text_layer, mask=mask_layer)
        if outputsize is not None:
            out.thumbnail(outputsize)
        return out
