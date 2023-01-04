#!/bin/sh
#------------------------------------------------------------------------------
# macedon [CLI web service availability verifier]
# (c) 2023 A. Shavykin <0.delameter@gmail.com>
#------------------------------------------------------------------------------

PYTHONPATH=. venv/bin/python -m macedon "$@"
