import os
import re
import logging
from typing import Dict, Tuple,  List

from PIL import Image, ImageFont
import pyphen


from canvas import Canvas

logger = logging.getLogger(__file__)


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
    color = (20, 20, 10)

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
        self.canvas._fill = self.style.color

        # self._current_page = Image.new(
        #     "RGB", self.background_image.size, (255, 255, 255))

    def render(self):
        basename, ext = os.path.splitext(self._output)
        outfilename = "{}{:03d}{}"

        page = 1
        line = 1
        self.position = self.style.pages[page - 1]['start']

        assert self._input['element'] == 'document'

        self.canvas.start_page()
        self.canvas.font(self.font)
        self.canvas.translate(self.style.pages[page - 1]['start'])
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
            logger.debug(el)
            for child in el['children']:
                self.render_element(child)

    def render_code_span(self, el):
        logger.info("Render code span")
        logger.debug(el)

    def render_thematic_break(self, el):
        logger.info("Render thematic break")
        self.render_raw_text({'children': '--------------------'})

    def render_blank_line(self, data):
        logger.info("Render blank line")
        lh = self.font.getsize('A')[1]
        logger.debug(f"Lineheight = {lh}")
        self.render_line_break({'soft': False})

    def render_line_break(self, data):
        logger.info("Render line break")
        lh = self.font.getsize('A')[1]
        if not data['soft']:
            self.canvas.translate(
                (-self.canvas.x + self.style.pages[0]['start'][0], lh))

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

    def render_list_item(self, data):
        logger.info("Render list item")
        logger.debug(data)
        for child in data['children']:
            self.render_element(child)

    def render_list(self, data):
        logger.info("Render list")
        logger.debug(data)
        for idx, child in enumerate(data['children']):
            if data['ordered']:
                self.render_raw_text({'children': f"{idx + data['start']}. "})
            else:
                self.render_raw_text({'children': f"{data['bullet']} "})
            self.render_element(child)
