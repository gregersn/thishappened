import os
from PIL import Image, ImageFont

from typing import Any, Tuple, cast
from thishappened.renderer.page import PageStyle
from thishappened.renderer.types import BlankLineData, CodeSpanData, DocumentData, EmphasisData, HeadingData, LineBreakData, ListData, ListItemData, MDElement, ParagraphData, RawTextData, StrongEmphasisData

from thishappened.renderer.canvas import Canvas

from thishappened.renderer.utils import text_warp

import logging

logger = logging.getLogger(__file__)


class MDRenderer():
    style: PageStyle
    canvas: Canvas

    def __init__(self, input: DocumentData,
                 output: str = 'output.png',
                 variation: Tuple[int, int] = (0, 0),
                 outputsize: Tuple[int, int] = (800, 1200),
                 lang: str = 'en',
                 style: PageStyle = PageStyle()):
        self._input = input
        self._page: int = 0
        self._column: int = 0
        self._line: int = 0
        self._output = output
        self._variation = variation
        self._outputsize = outputsize
        self._lang = lang
        self.style = style
        self.position: Tuple[int, int] = (0, 0)

        self.font = ImageFont.truetype(os.path.join(
            'assets', self.style.font), self.style.text_size)

        self.line_width = self.style.calculate_line_width(self.font.getsize)

        if self.style.background is not None:
            self.background_image = Image.open(os.path.join(
                'assets', self.style.background))
        else:
            self.background_image = Image.new(
                'RGB', size=outputsize, color=(255, 255, 255))

        self.canvas = Canvas(self.background_image.size)
        self.canvas.background(self.background_image)
        self.canvas.fill = self.style.color

        # self._current_page = Image.new(
        #     "RGB", self.background_image.size, (255, 255, 255))

    def render(self):
        basename, ext = os.path.splitext(self._output)
        outfilename = "{}{:03d}{}"

        self.position = self.style.pages[self._page - 1]['start']

        assert self._input['element'] == 'document'

        self.start_page()
        for el in self._input['children']:
            self.render_element(el)

        self.canvas.end_page()
        out = self.canvas.get()

        filename = outfilename.format(basename, self._page, ext)
        print("Saving...{}".format(filename))
        out.save(filename)
        # out.show()

    def start_page(self):
        self.canvas.start_page()
        self.canvas.font(self.font)
        self.canvas.translate(self.style.pages[self._page - 1]['start'])

    def end_column(self):
        pass

    def end_page(self):
        pass

    def render_element(self, el: MDElement):
        element = el['element']
        if hasattr(self, f'render_{element}'):
            f = getattr(self, f'render_{element}')
            f(el)
        else:
            print(f"Unknown element: {element}")
            logger.debug(el)
            for child in el.get('children', []):
                if isinstance(child, str):
                    print("There was an unexpected string")
                else:
                    self.render_element(child)

    def render_code_span(self, el: CodeSpanData):
        logger.info("Render code span")
        self.render_raw_text(cast(RawTextData, el))

    def render_thematic_break(self, el: Any):
        logger.info("Render thematic break")
        self.render_raw_text(
            {'element': 'raw_text', 'children': '--------------------', 'escape': False})

    def render_blank_line(self, data: BlankLineData):
        logger.info("Render blank line")
        lh = self.font.getsize('A')[1]
        logger.debug(f"Lineheight = {lh}")
        self.render_line_break({'element': 'line_break', 'soft': False})

    def render_line_break(self, data: LineBreakData):
        logger.info("Render line break")
        lh = self.font.getsize('A')[1]
        if not data['soft']:
            self.canvas.translate(
                (-self.canvas.x + self.style.pages[0]['start'][0], lh))

    def render_paragraph(self, data: ParagraphData):
        logger.info("Render paragraph")
        self.font_size = self.style.text_size

        for child in data['children']:
            self.render_element(child)

        self.render_line_break({'element': 'line_break', 'soft': False})

    def render_emphasis(self, data: EmphasisData):
        logger.info("Render emphasis")
        prev_font = self.font

        if self.style.font_italic is not None:
            self.font = ImageFont.truetype(os.path.join(
                'assets', self.style.font_italic), self.font_size)

        for child in data['children']:
            self.render_element(child)

        self.font = prev_font

    def render_strong_emphasis(self, data: StrongEmphasisData):
        logger.info("Render strong emphasis")
        prev_font = self.font

        if self.style.font_bold is not None:
            self.font = ImageFont.truetype(os.path.join(
                'assets', self.style.font_bold), self.font_size)

        for child in data['children']:
            self.render_element(child)

        self.font = prev_font

    def render_heading(self, data: HeadingData):
        level = data['level']
        logger.info(f"Render heading {level}")
        self.font_size = self.style.header_size[level - 1]
        prev_font = self.font

        self.font = ImageFont.truetype(os.path.join(
            'assets', self.style.font), self.font_size)

        for child in data['children']:
            self.render_element(child)
        self.render_line_break({'element': 'line_break', 'soft': False})

        self.font = prev_font

    def render_raw_text(self, data: RawTextData):
        logger.info("Render raw text")
        logger.debug(repr(data['children']))
        self.canvas.font(self.font)
        text = text_warp(data['children'], self.style.linelength *
                         self.style.text_size // self.font_size)

        self.canvas.text(text[0], self.line_width)

        # If there is more than one line, we need some line breaks and stuff.
        for line in text[1:]:
            self.render_line_break({'element': 'line_break', 'soft': False})
            self.canvas.text(line, self.line_width)

        self.position = (
            self.position[0], self.position[1] + self.font_size * (len(text) - 1))

    def render_list_item(self, data: ListItemData):
        logger.info("Render list item")
        logger.debug(data)
        for child in data['children']:
            self.render_element(child)

    def render_list(self, data: ListData):
        logger.info("Render list")
        logger.debug(data)
        for idx, child in enumerate(data['children']):
            if data['ordered']:
                self.render_raw_text(
                    {'element': 'raw_text', 'children': f"{idx + data['start']}. ", 'escape': True})
            else:
                self.render_raw_text(
                    {'element': 'raw_text', 'children': f"{data['bullet']} ", 'escape': True})
            self.render_element(child)
