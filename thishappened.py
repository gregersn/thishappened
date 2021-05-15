import fileinput
import os
import sys
import json
import re
from PIL import Image, ImageFont, ImageDraw, ImageChops, ImageFilter
from typing import List, Tuple, Dict, Union
import random
import pyphen
import click
import marko
from marko.ast_renderer import ASTRenderer
import frontmatter


def multiline_text(text: List[str], pos: Tuple[int, int],
                   image: Image.Image, font, linespacing: int = 0, variation=(0, 0)) -> Image.Image:
    ctx: ImageDraw.ImageDraw = ImageDraw.Draw(image)

    text_size: Tuple[int, int] = ctx.textsize("A", font=font)
    lineheight: int = text_size[1] + linespacing

    for i, line in enumerate(text):
        offsetpos = (pos[0] + random.random() * variation[0],
                     pos[1] + random.random() * variation[1])
        ctx.text(offsetpos, line, font=font, fill=(20, 20, 10))
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


class PageStyle:
    text_size = 32
    heading_size = 40


class MDRenderer():
    def __init__(self, input: Dict, output='output.png', variation=(0, 0), outputsize=None, lang='en', settings={}):
        self._input = input
        self._page = 0
        self._line = 0
        self._output = output
        self._variation = variation
        self._outputsize = outputsize
        self._lang = lang
        self.settings = settings
        self.position: Tuple[int, int] = (0, 0)
        self.workingfolder = settings['workingfolder']

        self.style = PageStyle

        self.font = ImageFont.truetype(os.path.join(
            self.workingfolder, self.settings['font']), self.settings['fontsize'])

        self.background_image = Image.open(os.path.join(
            self.workingfolder, self.settings['background']))

        self._current_page = Image.new(
            "RGB", self.background_image.size, (255, 255, 255))

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

    def render(self):
        basename, ext = os.path.splitext(self._output)
        outfilename = "{}{:03d}{}"

        page = 1
        self.position = self.settings['pages'][page - 1]['start']

        self._current_page = Image.new(
            "RGB", self.background_image.size, (255, 255, 255))

        assert self._input['element'] == 'document'

        for el in self._input['children']:
            self.render_element(el)

        out = self.compose(self._current_page, outputsize=self._outputsize)
        filename = outfilename.format(basename, page, ext)
        print("Saving...{}".format(filename))
        out.save(filename)
        out.show()

    def render_element(self, el):
        element = el['element']
        if hasattr(self, f'render_{element}'):
            f = getattr(self, f'render_{element}')
            f(el)
        else:
            print(f"Unknown element {element}")

    def render_blank_line(self, data):
        print("Render blank line")
        self.position = (self.position[0],
                         self.position[1] + self.style.text_size)

    def render_paragraph(self, data):
        print("Render paragraph")

        self.font_size = self.style.text_size

        for child in data['children']:
            self.render_element(child)

    def render_heading(self, data):
        print("Render heading")
        level = data['heading']
        self.font_size = self.style.heading_size
        for child in data['children']:
            self.render_element(child)

    def render_raw_text(self, data):
        print("Render raw text")

        self.font = ImageFont.truetype(os.path.join(
            self.workingfolder, self.settings['font']), self.font_size)

        text = text_warp(data['children'], self.settings['linelength'])

        self._current_page = multiline_text(
            text, self.position, self._current_page, self.font, self.settings['linespacing'], variation=self._variation)

        self.position = (
            self.position[0], self.position[1] + self.font_size * len(text))


class Generator():
    def __init__(self, settings):
        self.settings = settings
        self.workingfolder = settings['workingfolder']

        self.font = ImageFont.truetype(os.path.join(
            self.workingfolder, self.settings['font']), self.settings['fontsize'])

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

        return self.generate_plain(input, output, variation, outputsize, lang)

    def generate_ast(self, input: Dict, output='output.png', variation=(0, 0), outputsize=None, lang='en'):
        renderer = MDRenderer(input, output, variation,
                              outputsize, lang, self.settings)
        renderer.render()
        """
        text = text_warp(text, self.settings['linelength'])
        text_layer = Image.new(
            "RGB", self.background_image.size, (255, 255, 255))

        linespacing = self.settings['linespacing']

        while line < len(text):
            lines = self.settings['pages'][page %
                                           len(self.settings['pages'])]['lines']
            start = self.settings['pages'][page %
                                           len(self.settings['pages'])]['start']
            print(f"Page: {page}, start: {start}, lines {lines}")

            text_layer = multiline_text(text[line:line + lines], start,
                                        text_layer, self.font, linespacing,
                                        variation=variation)
            line += lines
            page += 1

            if page > 0 and (page % len(self.settings['pages'])) == 0 and line < (len(text) - 1):
                filename = outfilename.format(basename, page, ext)
                print("Saving (in loop)...{}".format(filename))
                out = self.compose(text_layer, outputsize=outputsize)
                out.save(filename)
                text_layer = Image.new(
                    "RGB", self.background_image.size, (255, 255, 255))
    
        out = self.compose(text_layer, outputsize=outputsize)
        filename = outfilename.format(basename, page, ext)
        print("Saving...{}".format(filename))
        out.save(filename)
        out.show()
        """

    def generate_plain(self, input_text: str, output='output.png', variation=(0, 0), outputsize=None, lang='en'):
        page = 0
        line = 0

        basename, ext = os.path.splitext(output)
        outfilename = "{}{:03d}{}"

        text = text_warp(input_text, self.settings['linelength'])
        text_layer = Image.new(
            "RGB", self.background_image.size, (255, 255, 255))

        linespacing = self.settings['linespacing']

        while line < len(text):
            lines = self.settings['pages'][page %
                                           len(self.settings['pages'])]['lines']
            start = self.settings['pages'][page %
                                           len(self.settings['pages'])]['start']
            print(f"Page: {page}, start: {start}, lines {lines}")

            text_layer = multiline_text(text[line:line + lines], start,
                                        text_layer, self.font, linespacing,
                                        variation=variation)
            line += lines
            page += 1

            if page > 0 and (page % len(self.settings['pages'])) == 0 and line < (len(text) - 1):
                filename = outfilename.format(basename, page, ext)
                print("Saving (in loop)...{}".format(filename))
                out = self.compose(text_layer, outputsize=outputsize)
                out.save(filename)
                text_layer = Image.new(
                    "RGB", self.background_image.size, (255, 255, 255))

        out = self.compose(text_layer, outputsize=outputsize)
        filename = outfilename.format(basename, page, ext)
        print("Saving...{}".format(filename))
        out.save(filename)
        out.show()


def load_asset(filename: str):
    assert os.path.isfile(filename), filename
    settings = {}
    with open(filename, 'r') as f:
        settings = json.load(f)

    settings['workingfolder'] = os.path.dirname(filename)

    return settings


@click.command()
@click.option('--markdown', help="Markdown file to use")
def main(markdown: str):
    if markdown:
        data = frontmatter.load(markdown)
        settings = load_asset('assets/' + data['settings'])
        text = data.content

        m = marko.Markdown(renderer=ASTRenderer)
        text = m.convert(data.content)

    else:
        text = sys.stdin.read()
        settings = load_asset(sys.argv[1])

    generator = Generator(settings)
    generator.generate(text, "output.png", variation=(
        20, 10), outputsize=800, lang='en')


if __name__ == "__main__":
    main()
