import fileinput
import os
import sys
import json
import re
from PIL import Image, ImageFont, ImageDraw, ImageChops, ImageFilter
from typing import List, Tuple
import random
import pyphen

def multiline_text(text: List[str], pos: Tuple[int, int],
                   image: Image, font, linespacing=0, variation=(0, 0)):
    ctx = ImageDraw.Draw(image)

    linespacing =  ctx.textsize("A", font=font)[1] + linespacing
    
    for i, line in enumerate(text):
        offsetpos = (pos[0] + random.random() * variation[0], pos[1] + random.random() * variation[1])
        ctx.text(offsetpos, line, font=font, fill=(0, 0, 0))
        pos = (pos[0], pos[1] + linespacing)

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

    words = re.findall(r'\S+|\n',text)
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


class Generator():
    def __init__(self, settings):
        self.settings = settings
        self.workingfolder = settings['workingfolder']
        
        self.font = ImageFont.truetype(os.path.join(self.workingfolder, self.settings['font']), self.settings['fontsize'])

        self.background_image = Image.open(os.path.join(self.workingfolder, self.settings['background']))
    
    def compose(self, overlay, outputsize=None):
        out = self.background_image.copy()
        text_layer = ImageChops.overlay(overlay, self.background_image.copy().convert('RGB'))
        mask_layer = text_layer.copy()
        mask_layer = mask_layer.convert('L')
        mask_layer = ImageChops.invert(mask_layer)
        mask_layer = mask_layer.filter(ImageFilter.GaussianBlur(1))

        out.paste(text_layer, mask=mask_layer)
        if outputsize is not None:
            out.thumbnail((outputsize, outputsize))
        return out


    def generate(self, text: str, output='output.png', variation=(0, 0), outputsize=None, lang='en'):
        page = 0
        line = 0

        basename, ext = os.path.splitext(output)
        outfilename = "{}{:03d}{}"
        
        text = text_warp(text, self.settings['linelength'])
        text_layer = Image.new("RGB", self.background_image.size, (255, 255, 255))

        linespacing = self.settings['linespacing']

        while line < len(text):
            lines = self.settings['pages'][page % len(self.settings['pages'])]['lines']
            start = self.settings['pages'][page % len(self.settings['pages'])]['start']
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
                text_layer = Image.new("RGB", self.background_image.size, (255, 255, 255))

        out = self.compose(text_layer, outputsize=outputsize)
        filename = outfilename.format(basename, page, ext)
        print("Saving...{}".format(filename))
        out.save(filename)
        out.show()


def load_asset(filename: str):
    assert os.path.isfile(filename)
    settings = {}
    with open(filename, 'r') as f:
        settings = json.load(f)
    
    settings['workingfolder'] = os.path.dirname(filename)

    return settings


def main():
    text = sys.stdin.read()
    
    settings = load_asset(sys.argv[1])
    generator = Generator(settings)
    generator.generate(text, "output.png", variation=(0, 7), outputsize=1000, lang='en')


if __name__ == "__main__":
    main()
