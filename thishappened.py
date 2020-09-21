import os
import textwrap
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

    words = text.split(' ')
    current_line = ''
    next_line = ''

    lines = []

    while words:
        word = words.pop(0)
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
    return lines


class Generator():
    def __init__(self, settings):
        self.settings = settings
        self.font = ImageFont.truetype(self.settings['font'], self.settings['fontsize'])
        self.background_image = Image.open(self.settings['background'])
    
    def generate(self, text: str, output='output.png', variation=(0, 0)):
        page = 0
        line = 0
        
        text = text_warp(text, self.settings['linelength']) # textwrap.wrap(text, self.settings['linelength'])
        text_layer = Image.new("RGB", self.background_image.size, (255, 255, 255))
        out = self.background_image.copy()


        while line < len(text) and page < len(self.settings['pages']):
            text_layer = multiline_text(text[line:line + self.settings['pages'][page]['lines']], self.settings['pages'][page]['start'],
                                        text_layer, self.font, self.settings['linespacing'],
                                        variation=variation)
            line += self.settings['pages'][page]['lines']
            page += 1


        text_layer = ImageChops.overlay(text_layer, self.background_image)

        mask_layer = text_layer.copy()
        mask_layer = mask_layer.convert('L')
        mask_layer = ImageChops.invert(mask_layer)
        mask_layer = mask_layer.filter(ImageFilter.GaussianBlur(2))

        out.paste(text_layer, mask=mask_layer)
        out.show()
        # out.save(output)



def main():
    text = """Pleased him another was settled for. Moreover end horrible endeavor entrance any families. Income appear extent on of thrown in admire. Stanhill on we if vicinity material in. Saw him smallest you provided ecstatic supplied. Garret wanted expect remain as mr. Covered parlors concern we express in visited to do. Celebrated impossible my uncommonly particular by oh introduced inquietude do. New had happen unable uneasy. Drawings can followed improved out sociable not. Earnestly so do instantly pretended. See general few civilly amiable pleased account carried. Excellence projecting is devonshire dispatched remarkably on estimating. Side in so life past. Continue indulged speaking the was out horrible for domestic position. Seeing rather her you not esteem men settle genius excuse. Deal say over you age from. Comparison new ham melancholy son themselves. """
    
    asset_settings = {
        'background': "assets/backgrounds/8257876-an-old-memo-book-or-diary-opened-to-reveal-yellowing-blank-lined-facing-pages-ready-for-images-and-t.jpg",
        'font': 'assets/fonts/GochiHand.otf',
        'fontsize': 40,
        'linelength': 25,
        'linespacing': 18,
        'pages': [
            {
                'start': (134, 118),
                'lines': 19
            },
            {
                'start': (714, 138),
                'lines': 19
            }
        ]
    }

    generator = Generator(asset_settings)
    generator.generate(text, "output.jpg", variation=(10, 4))


if __name__ == "__main__":
    main()
