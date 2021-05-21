import os
import json
from typing import List, Tuple
import click
import marko
from marko.ast_renderer import ASTRenderer
import frontmatter
import logging

from mdrender import MDRenderer, PageStyle


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__file__)


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
    assert os.path.isfile(markdown)

    data = frontmatter.load(markdown)
    if data.get('settings', None):
        settings = load_asset('assets/' + data['settings'])
    else:
        settings = {}
    text = data.content
    style = PageStyle(settings)

    MDRenderer.style = style

    m = marko.Markdown(renderer=ASTRenderer)
    text = m.convert(data.content)

    style = PageStyle(settings)
    renderer = MDRenderer(text, "output.png", variation=(0, 0),
                          outputsize=(1600, 2400), lang='en', settings=settings)
    renderer.render()


if __name__ == "__main__":
    main()
