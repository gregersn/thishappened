import re
import pyphen

from typing import Optional, List, Tuple

import logging

logger = logging.getLogger("thishappened")


def text_warp(text: str,
              line_length: int,
              language: Optional[str] = None) -> List[str]:
    logger.debug(f"Wrapping text at {line_length} length")
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


def text_grab(text: str,
              line_length: int,
              language: Optional[str] = None) -> Tuple[str, Optional[str]]:
    logger.debug(f"Wrapping text at {line_length} length")
    pyphen.language_fallback('en')
    dic = pyphen.Pyphen(lang='en')

    if language is not None:
        dic = pyphen.Pyphen(lang=language)

    current_line: str = ''

    words = re.findall(r'\S+|\n', text)
    words = words[::-1]
    while words:
        word = words.pop(-1)
        if word == '\n':
            return current_line, " ".join(words[::-1])

        if len(current_line + word) <= line_length:
            current_line += word + ' '
            continue

        split = dic.wrap(word, line_length - len(current_line))

        if split is not None:
            current_line += split[0] + ' '
            words = [split[1]] + words[::-1]
        else:
            words = [word] + words[::-1]

        return current_line.strip(), " ".join(words)

    return current_line.strip(), None