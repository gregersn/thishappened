import fileinput
import os
import sys
import json
import re
from PIL import Image, ImageFont, ImageDraw, ImageChops, ImageFilter
from typing import List, NamedTuple, Tuple, Dict, Union
from collections import namedtuple
import random
import pyphen
import click
import marko
from marko.ast_renderer import ASTRenderer
import frontmatter
import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__file__)


def multiline_text(text: List[str], pos: Tuple[int, int],
                   image: Image.Image, font, linespacing: int = 0, variation=(0, 0), color=(20, 20, 10)) -> Image.Image:
    ctx: ImageDraw.ImageDraw = ImageDraw.ImageDraw(image)

    text_size: Tuple[int, int] = font.getsize(
        "A")
    lineheight: int = text_size[1] + linespacing

    logger.debug(f"Variation is {variation}")
    for i, line in enumerate(text):
        offsetpos = (pos[0] + random.random() * variation[0],
                     pos[1] + random.random() * variation[1])
        ctx.text(offsetpos, line, font=font, fill=color)
        pos = (pos[0], pos[1] + lineheight)

    return image


def text_warp(text: str, line_length: int, language=None) -> List[str]:
    pyphen.language_fallback('en')
    dic = pyphen.Pyphen(lang='en')

    if language is not None:
        dic = pyphen.Pyphen(lang=language)

    words = text.split(' ')
    current_line = ''
    next_line = ''

    lines = []

    words = re.findall(r'\S+|\n', text)
    words = words[::-1]
    while words:
        word = words.pop(-1)
        if word == '\n':
            lines.append(current_line)
            current_line = next_line
            next_line = ''
            continue

        if len(current_line + word) < line_length:
            current_line += word + ' '
            continue

        split = dic.wrap(word, line_length - len(current_line))

        if split is not None:
            current_line += split[0] + ' '
            next_line += split[1] + ' '
        else:
            next_line += word + ' '

        lines.append(current_line)
        current_line = next_line
        next_line = ''
    lines.append(current_line)
    return lines


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
    linelength = 80
    linespacing = 0
    pages = [
        {
            "start": (64, 100),
            "lines": 60
        }
    ]
    ink = (20, 20, 10)

    def __init__(self, d: Dict = {}):
        self.__dict__.update(**d)


class MDRenderer():
    style: PageStyle = PageStyle()
    canvas: Canvas

    def __init__(self, input: Dict, output='output.png', variation=(0, 0), outputsize: Tuple[int, int] = (800, 1200), lang='en', settings={}):
        self._input = input
        self._page = 0
        self._line = 0
        self._output = output
        self._variation = variation
        self._outputsize = outputsize
        self._lang = lang
        self.position: Tuple[int, int] = (0, 0)

        self.font = ImageFont.truetype(os.path.join(
            'assets', self.style.font), self.style.text_size)

        if self.style.background is not None:
            self.background_image = Image.open(os.path.join(
                'assets', self.style.background))
        else:
            self.background_image = Image.new(
                'RGB', size=outputsize, color=(255, 255, 255))

        self.canvas = Canvas(self.background_image.size)
        self.canvas.background(self.background_image)

        # self._current_page = Image.new(
        #     "RGB", self.background_image.size, (255, 255, 255))

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

    def render(self):
        basename, ext = os.path.splitext(self._output)
        outfilename = "{}{:03d}{}"

        page = 1
        self.position = self.style.pages[page - 1]['start']

        assert self._input['element'] == 'document'

        self.canvas.start_page()
        self.canvas.font(self.font)
        for el in self._input['children']:
            self.render_element(el)

        self.canvas.end_page()
        out = self.canvas.get()

        filename = outfilename.format(basename, page, ext)
        print("Saving...{}".format(filename))
        out.save(filename)
        # out.show()

    def render_element(self, el):
        element = el['element']
        if hasattr(self, f'render_{element}'):
            f = getattr(self, f'render_{element}')
            f(el)
        else:
            print(f"Unknown element: {element}")
            for child in el['children']:
                self.render_element(child)

    def render_blank_line(self, data):
        logger.info("Render blank line")
        lh = self.font.getsize('A')[1]
        logger.debug(f"Lineheight = {lh}")
        self.render_line_break({'soft': False})

    def render_line_break(self, data):
        logger.info("Render line break")
        lh = self.font.getsize('A')[1]
        if not data['soft']:
            self.canvas.translate((-self.canvas.x, lh))

    def render_paragraph(self, data):
        logger.info("Render paragraph")
        self.font_size = self.style.text_size

        for child in data['children']:
            self.render_element(child)

        self.render_line_break({'soft': False})

    def render_emphasis(self, data):
        logger.info("Render emphasis")
        prev_font = self.font

        if self.style.font_italic is not None:
            self.font = ImageFont.truetype(os.path.join(
                'assets', self.style.font_italic), self.font_size)

        for child in data['children']:
            self.render_element(child)

        self.font = prev_font

    def render_strong_emphasis(self, data):
        logger.info("Render strong emphasis")
        prev_font = self.font

        if self.style.font_bold is not None:
            self.font = ImageFont.truetype(os.path.join(
                'assets', self.style.font_bold), self.font_size)

        for child in data['children']:
            self.render_element(child)

        self.font = prev_font

    def render_heading(self, data):
        level = data['level']
        logger.info(f"Render heading {level}")
        self.font_size = self.style.header_size[level - 1]
        prev_font = self.font

        self.font = ImageFont.truetype(os.path.join(
            'assets', self.style.font), self.font_size)

        for child in data['children']:
            self.render_element(child)
        self.render_line_break({'soft': False})

        self.font = prev_font

    def render_raw_text(self, data):
        logger.info("Render raw text")
        logger.debug(repr(data['children']))
        self.canvas.font(self.font)
        text = text_warp(data['children'], self.style.linelength)

        self.canvas.text(text[0])

        # If there is more than one line, we need some line breaks and stuff.
        for line in text[1:]:
            self.render_line_break({'soft': False})
            self.canvas.text(line)

        self.position = (
            self.position[0], self.position[1] + self.font_size * (len(text) - 1))


class Generator():
    def __init__(self, settings, style=PageStyle):
        self.settings = settings
        self.style = style
        self.workingfolder = settings.get(
            'workingfolder', os.path.abspath(__file__))

        print(f"Setting font to {self.style.font}")
        self.font = ImageFont.truetype(os.path.join(
            self.workingfolder, self.style.font), self.style.text_size)

        if self.style.background is not None:
            self.background_image = Image.open(os.path.join(
                self.workingfolder, self.settings['background']))

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
            out.thumbnail((outputsize, outputsize))
        return out

    def generate(self, input: Union[str, Dict], output='output.png', variation=(0, 0), outputsize=None, lang='en'):
        if isinstance(input, Dict):
            return self.generate_ast(input, output, variation, outputsize, lang)

    def generate_ast(self, input: Dict, output='output.png', variation=(0, 0), outputsize=None, lang='en'):
        renderer = MDRenderer(input, output, variation,
                              outputsize, lang, self.settings)
        renderer.render()


def load_asset(filename: str):
    assert os.path.isfile(filename), filename
    settings = {}
    with open(filename, 'r') as f:
        settings = json.load(f)

    settings['workingfolder'] = os.path.dirname(filename)

    return settings


@click.command()
@click.argument('markdown')
def main(markdown: str):
    data = frontmatter.load(markdown)
    if data.get('settings', None):
        settings = load_asset('assets/' + data['settings'])
    else:
        settings = {}
    text = data.content
    style = PageStyle(settings)

    MDRenderer.style = style
    print(style.text_size)
    m = marko.Markdown(renderer=ASTRenderer)
    text = m.convert(data.content)

    style = PageStyle(settings)
    generator = Generator(settings, style)
    generator.generate(text, "output.png", variation=(
        0, 0), outputsize=(1600, 2400), lang='en')


if __name__ == "__main__":
    main()
