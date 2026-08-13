# Reference: https://github.com/adrienbrignon/mkdocs-exporter/issues/46#issuecomment-2479847642

import markdown
from bs4 import BeautifulSoup
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.structure.nav import Section, get_navigation
from mkdocs.structure.pages import Page


def _get_page_toc(page: Page) -> str:
    """
    Generate the HTML unordered list part of the Table of Contents for `page`.

    Args:
        page (Page): The page to create a Table of Contents from

    Returns:
        str: An HTML unordered list
    """
    content = ""
    url = page.file.abs_src_path
    with open(url, "r") as file:
        # render markdown file
        page_toc = markdown.Markdown(
            extensions=["toc", "fenced_code", "md_in_html", "attr_list", "meta"]
        )
        page_toc.convert(file.read())
        content: str = page_toc.toc
        # add page path to anchor links
        content = content.replace('="#', '="' + page.file.dest_path + "#")
        # extract only the unordered list
        soup = BeautifulSoup(content, "html.parser")
        content = str(soup.find("ul"))

    return content


def _nav_to_html(nav_items: list) -> str:
    """
    Converts the MkDocs Navigation.items into an HTML string

    Args:
        nav_items (list): The contents of the `items` property of a Navigation object.

    Returns:
        str: A representation of the Navigation as an HTML string
    """
    content = []
    for item in nav_items:
        if isinstance(item, Page):
            if item.markdown is None:
                item.markdown = ""
            title = item.title
            if title is not None:
                content.append('<li><a href="' + item.url + '">' + title + "</a>")
                content.append(_get_page_toc(item))
                content.append("</li>")
        if isinstance(item, Section):
            content.append("<li>")
            if isinstance(item.title, str):
                content.append(item.title.capitalize())
            content.append(_nav_to_html(item.children))
            content.append("</li>")

    content.insert(0, "<ul>")
    content.append("</ul>")
    return "\n".join(content)


def on_files(files: Files, config: MkDocsConfig):
    """
    Invoked when files are ready to be manipulated.

    Args:
        files (Files): The collection of files.
        config (Config): The site configuration.

    Returns:
        Files: The files collection
    """
    nav = get_navigation(files, config)
    content = (
        '<div class="toc"><span class="toctitle site_toc">Table of Contents</span>'
        + _nav_to_html(nav.items)
        + "</div>"
    )
    # Create a virtual file from generated text
    file = File.generated(
        config,
        "generated_site_toc.md",
        content=content,
        inclusion=InclusionLevel.INCLUDED,
    )
    # Add the virtual file to the site files
    files.append(file)
    # Add the virtual file to the site navigation with empty text for the title to hide it when viewing the website.
    config.nav.insert(0, {"": "generated_site_toc.md"})

    return files
