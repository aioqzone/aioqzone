# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "aioqzone"
copyright = "2022-2023, aioqzone"
author = "aioqzone"

# The full version, including alpha/beta/rc tags
release = "0.1.0"  # This should be overwritten by command line options (-D).


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.githubpages",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# internationalization
language = "zh_CN"
locale_dirs = ["locale/"]
gettext_compact = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"
html_logo = "./_static/penguin-blob.webp"
html_favicon = html_logo

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# autodoc_pydantic settings
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_undoc_members = False
autodoc_member_order = "bysource"

# external inventory
intersphinx_mapping = {
    # "httpx": ("https://www.python-httpx.org/", None),
    "python": ("https://docs.python.org/3/", None),
}
