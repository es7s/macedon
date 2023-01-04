# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022. A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------

from .entrypoint import invoke as entrypoint_fn
from ._version import __version__

APP_NAME = "macedon"
APP_VERSION = __version__
