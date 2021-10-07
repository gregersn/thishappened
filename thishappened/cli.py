from typing import Any, Dict, Union
import click
from pathlib import Path
import marko
from marko.ast_renderer import ASTRenderer
import frontmatter


from thishappened.renderer.mdrenderer import MDRenderer, PageStyle
from thishappened import Styling, load_asset

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
