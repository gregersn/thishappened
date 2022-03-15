from typing import Any, Dict, Union, cast
import click
from pathlib import Path
import marko
from marko.ast_renderer import ASTRenderer
import frontmatter

from thishappened.renderer.mdrenderer import MDRenderer, PageStyle
from thishappened import Styling, load_asset
from thishappened.renderer.types import DocumentData


@click.command()
@click.argument('markdown', type=click.Path(path_type=Path, exists=True))
def main(markdown: Path):
    """Render markdown file to an image.
    
    MARKDOWN: Path to markdown file.
    """
    # Load the markdown file
    data = frontmatter.load(str(markdown.resolve()))

    # Get path to settings file if one is defined
    settings_file: Union[str, None] = data.get('settings', None)
    if isinstance(settings_file, str):
        # Settings file is defined
        if (markdown.parent / settings_file).is_file():
            filename = markdown.parent / settings_file
        elif (Path('assets') / settings_file).is_file():
            filename = Path('assets') / settings_file
        else:
            raise Exception("No settings file found.")
        settings = load_asset(filename)
    else:
        # The settings are defined right into the markdown.
        settings: Dict[str, Any] = dict(data)

    # Grab the actual markdown content.
    text = data.content

    assert isinstance(settings, dict)
    # Convert the settings dict into an object
    style = PageStyle(settings)

    print(style)

    # Set the style in the markdown renderer object.
    MDRenderer.style = style

    # Convert markdown to an AST.
    m = marko.Markdown(renderer=ASTRenderer, extensions=[Styling])
    text = cast(DocumentData, m.convert(data.content))

    renderer = MDRenderer(text,
                          markdown.with_suffix(".png"),
                          lang='no',
                          style=style)
    renderer.render()


if __name__ == "__main__":
    main()
