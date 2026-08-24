"""Thiết lập console UTF-8 nhất quán trên Windows và các CI runner."""
import sys


def configure_utf8_console() -> None:
    """Cho phép in tiếng Việt/emoji mà không phụ thuộc code page hệ thống."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
