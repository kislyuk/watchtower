import os

project = "watchtower"
copyright = "Andrey Kislyuk"
author = "Andrey Kislyuk"
version = ""
release = ""
language = "en"
master_doc = "index"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.intersphinx", "sphinx_copybutton"]
source_suffix = [".rst", ".md"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
autodoc_typehints = "description"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
templates_path = [""]

if "readthedocs.org" in os.getcwd().split("/"):
    with open("index.rst", "w") as fh:
        fh.write("Documentation for this project has moved to https://kislyuk.github.io/" + project)
else:
    html_theme = "furo"
    html_sidebars = {
        "**": [
            "sidebar/brand.html",
            "sidebar/search.html",
            "sidebar/scroll-start.html",
            "toc.html",
            "sidebar/scroll-end.html",
        ]
    }
