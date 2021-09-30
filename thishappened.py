import os
import json
from typing import Any, Dict, Union
import click
import marko
from marko.ast_renderer import ASTRenderer
import frontmatter
import logging

from thishappened.renderer.mdrenderer import MDRenderer, PageStyle


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
@click.argument('markdown')
def main(markdown: str):
    assert os.path.isfile(markdown)

    data = frontmatter.load(markdown)
    settings_file: Union[str, None] = data.get('settings', None)
    if isinstance(settings_file, str):
        settings = load_asset('assets/' + settings_file)
    else:
        settings: Dict[str, Any] = dict(data)
    text = data.content

    assert isinstance(settings, dict)
    style = PageStyle(settings)

    MDRenderer.style = style

    m = marko.Markdown(renderer=ASTRenderer)
    text = m.convert(data.content)

    style = PageStyle(settings)
    renderer = MDRenderer(text, "output.png", variation=(0, 0),
                          outputsize=(1500, 400), lang='en', style=style)
    renderer.render()


if __name__ == "__main__":
    main()
