"""UP (uin-password) login package.

Exports :class:`UpWebLogin` and :class:`UpH5Login`.
"""

from .h5 import UpH5Login
from .web import UpWebLogin

__all__ = ["UpH5Login", "UpWebLogin"]
