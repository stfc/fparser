# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import subprocess
import fparser

project = 'fparser'
copyright = '2017-2024, Science and Technology Facilities Council'
author = 'Andrew Porter, Rupert Ford, Balthasar Reuter and Pearu Peterson'

version = fparser._get_version()
release = fparser._get_version()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.viewcode',
    'autoapi.extension',
]

autoapi_dirs = ['../../src']
autoapi_ignore = ['*test_*']
autoapi_keep_files = True

templates_path = ['_templates']
exclude_patterns = []

root_doc = 'index'

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
# We specify the directory containing the doxygen output (as configured in
# ../doxygen.config) so that we can link to it from index.rst.
html_static_path = ['doxygen']

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Generate the Doxygen documentation
subprocess.call('cd ..; doxygen doxygen.config', shell=True)
