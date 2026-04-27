"""Tiện ích in Excel qua máy in Windows.

Module gói các dependency ``win32api`` / ``win32print`` sao cho import
được trên Linux/CI mà không phát sinh lỗi — việc in chỉ khả dụng trên máy
Windows đã cài ``pywin32``.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

try:  # pragma: no cover - phụ thuộc Windows
    import win32api  # type: ignore
except ImportError:  # pragma: no cover
    win32api = None  # type: ignore


class PrinterUnavailable(RuntimeError):
    """Raised khi hệ điều hành không hỗ trợ in qua pywin32."""


def print_excel_to(printer_name: str, file_path: str) -> None:
    """Gửi ``file_path`` tới ``printer_name`` rồi xóa file tạm."""
    if win32api is None:
        raise PrinterUnavailable(
            "Chức năng in chỉ khả dụng trên Windows với pywin32."
        )

    try:
        win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
    finally:
        try:
            os.unlink(file_path)
        except OSError as exc:
            logger.warning("Không thể xóa file in tạm %s: %s", file_path, exc)
