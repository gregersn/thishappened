from typing import Match, Dict, Any

import os
import json
import logging
from pathlib import Path

from marko.inline import InlineElement


class StyleCommand(InlineElement):
    pattern = r'\[\[\!(\w+):\s+(\w+)\]\][\r\n]*'

    def __init__(self, match: Match[str]):
        logger.debug("Found a stylecommand")
        self.property = match.group(1)
        self.value = match.group(2)


class Styling:
    elements = [StyleCommand]


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__file__)


def load_asset(filename: Path) -> Dict[str, Any]:
    assert filename.is_file()
    settings = {}
    with open(filename, 'r') as f:
        settings = json.load(f)

    settings['workingfolder'] = os.path.dirname(filename)

    return settings
