import os
import sys

# -- Path setup ---------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

sys.path.insert(0, os.path.abspath('..'))
root_doc = 'index'

# -- Project information ------------------------------------------------------

project = '*PROJECT_NAME'
copyright = '*CYR, Alexandr Shavykin'
author = 'Alexandr Shavykin'
show_authors = True

github_repository = '*PROJECT_NAME'
github_branch     = 'master'

import *PROJECT_NAME
version = *PROJECT_NAME.__version__
release = version

# -- General configuration ----------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',     'sphinx.ext.todo',
    'sphinx.ext.autosummary', 'sphinx.ext.extlinks',
    'sphinx.ext.viewcode',    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.doctest',
    'sphinx_copybutton',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = ['_build']

rst_prolog = """
.. role:: mono
    :class: entity
"""

# -- HTML ---------------------------------------------------------------------

html_theme = 'furo'

if len(version) > 5:
    html_title = f'*PROJECT_NAME<br>{version}'
else:
    html_title = f'*PROJECT_NAME {version}'

html_static_path = ['_static']
html_css_files = ['custom.css', 'custom-furo.css']
html_js_files = ['custom.js']
html_favicon = '_static/logo-96.png'  # @TODO svg
html_logo = '_static/logo-96.png'  # @TODO svg

html_theme_options = {
    "footer_icons": [
        {
            "name": "pypi",
            "url": "https://pypi.org/project/*PROJECT_NAME",
            "html": """
                <svg width="8.3862762mm" height="7.9437408mm" viewBox="0 0 8.3862762 7.9437408" version="1.1"> 
                    <g transform="translate(-70.327089,-65.242521)"><g transform="matrix(0.26458333,0,0,0.26458333,-104.4515,-52.03226)"> 
                        <path stroke-width="0.355076" d="m 660.75803,449.15562 15.55544,5.66172 15.78565,-5.74552 -15.55544,-5.66172 z" style="fill:currentColor;fill-opacity:0.4;stroke:currentColor;stroke-opacity:1.0" />
                        <path stroke-width="0.355076" d="m 676.31347,454.81734 v 18.28268 l 15.78565,-5.74551 v -18.28269 z" style="fill:currentColor;fill-opacity:0.37;stroke:currentColor;stroke-opacity:1.0" />
                        <path stroke-width="0.355076" d="m 660.75803,449.15562 15.55544,5.66172 v 18.28268 l -15.55544,-5.66171 z" style="fill:currentColor;fill-opacity:0.25;stroke:currentColor;stroke-opacity:1.0" />
                    </g></g>
                </svg>
            """,
            "class": "",
        },
        {
            "name": "github",
            "url": "https://github.com/*PROJECT_URL",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}


# -- LaTeX / PDF --------------------------------------------------------------

latex_logo = '_static/logo-96.png'

# -- autodoc ------------------------------------------------------------------

autodoc_default_options = {
    'members': True,
    'undoc-members': True,  # @TODO remove after active development is finished
    'inherited-members': True,
    'show-inheritance': True,
    'special-members': '__call__',
    'member-order': 'bysource',
}

autodoc_class_signature = 'separated'
autodoc_typehints = 'signature'

keep_warnings = True
nitpick_ignore = [('py:class', 'Match'),
                  ('py:class', 'InitVar'),
                 ]

# -- Misc ---------------------------------------------------------------------

todo_include_todos = True

# -- Hide "bases: object" elements --------------------------------------------

# ClassDocumenter.add_directive_header uses ClassDocumenter.add_line to write the class documentation.
# We'll monkeypatch the add_line method and intercept lines that begin with "Bases:".
# In order to minimize the risk of accidentally intercepting a wrong line, we'll apply this patch inside of the
# add_directive_header method.
# https://stackoverflow.com/a/46284013/5834973

from sphinx.ext.autodoc import ClassDocumenter, _

add_line = ClassDocumenter.add_line
line_to_delete = _(u'Bases: %s') % u':py:class:`object`'


def add_line_no_object_base(self, text, *args, **kwargs):
    if text.strip() == line_to_delete:
        return
    add_line(self, text, *args, **kwargs)


def add_directive_header_no_object_base(self, *args, **kwargs):
    self.add_line = add_line_no_object_base.__get__(self)
    result = add_directive_header(self, *args, **kwargs)  # noqa
    del self.add_line
    return result


add_directive_header = ClassDocumenter.add_directive_header
ClassDocumenter.add_directive_header = add_directive_header_no_object_base
