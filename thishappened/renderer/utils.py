import re
import pyphen

from typing import Optional, List

import logging

logger = logging.getLogger(__file__)


def text_warp(text: str, line_length: int, language: Optional[str] = None) -> List[str]:
    logger.info(f"Wrapping text at {line_length} length")
    pyphen.language_fallback('en')
    dic = pyphen.Pyphen(lang='en')

    if language is not None:
        dic = pyphen.Pyphen(lang=language)

    words = text.split(' ')
    current_line: str = ''
    next_line: str = ''

    lines: List[str] = []

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

        lines.append(current_line.strip())
        current_line = next_line
        next_line = ''
    lines.append(current_line)
    return lines
