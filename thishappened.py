import os
import json
from typing import Any, Dict, Match, Union
import click
from pathlib import Path
import marko
from marko.ast_renderer import ASTRenderer
from marko.inline import InlineElement
import frontmatter
import logging

from thishappened.renderer.mdrenderer import MDRenderer, PageStyle


class StyleCommand(InlineElement):
    pattern = r'\[\[\!(\w+):\s+(\w+)\]\][\r\n]*'

    def __init__(self, match:  Match[str]):
        logger.debug("Found a stylecommand")
        self.property = match.group(1)
        self.value = match.group(2)


class Styling:
    elements = [StyleCommand]


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__file__)


def load_asset(filename: str) -> Dict[str, Any]:
    assert os.path.isfile(filename), filename
    settings = {}
    with open(filename, 'r') as f:
        settings = json.load(f)

    settings['workingfolder'] = os.path.dirname(filename)

    return settings


@click.command()
@click.argument('markdown', type=click.Path(path_type=Path, exists=True))
def main(markdown: Path):
    data = frontmatter.load(str(markdown.resolve()))
    settings_file: Union[str, None] = data.get('settings', None)
    if isinstance(settings_file, str):
        settings = load_asset('assets/' + settings_file)
    else:
        settings: Dict[str, Any] = dict(data)
    text = data.content

    assert isinstance(settings, dict)
    style = PageStyle(settings)

    MDRenderer.style = style

    m = marko.Markdown(renderer=ASTRenderer, extensions=[Styling])
    text = m.convert(data.content)

    style = PageStyle(settings)
    renderer = MDRenderer(text, markdown.stem + ".png",
                          lang='en', style=style)
    renderer.render()


if __name__ == "__main__":
    main()
