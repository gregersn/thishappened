from typing import Tuple
from PIL import Image, ImageDraw, ImageChops, ImageFilter


class Canvas:
    _page: Image.Image
    _background: Image.Image
    _ctx: ImageDraw.ImageDraw
    _pos: Tuple[int, int]
    _fill: Tuple[int, int, int]

    def __init__(self, size: Tuple[int, int]):
        self._size = size
        self._pos = (0, 0)
        self._fill = (0, 0, 0)

    def font(self, font):
        self._font = font

    def pagebreak(self):
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

    def text(self, data: str):
        text_size: Tuple[int, int] = self._font.getsize(data)
        self._ctx.text(self._pos, data, font=self._font, fill=self._fill)
        self.translate((text_size[0], 0))

    def translate(self, offset: Tuple[int, int]):
        self._pos = (self._pos[0] + offset[0], self._pos[1] + offset[1])

    @property
    def x(self):
        return self._pos[0]

    @property
    def y(self):
        return self._pos[1]

    def compose(self, overlay, outputsize=None):
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
