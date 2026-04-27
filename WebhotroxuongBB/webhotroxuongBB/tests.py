"""Smoke tests chạy được mà không cần SQL Server / PostgreSQL thật.

Thiết lập ``USE_SQLITE_FALLBACK=1`` trước khi chạy ``manage.py test``
để Django dùng SQLite cho connection ``default``.
"""

from __future__ import annotations

import os

from django.conf import settings
from django.test import Client, TestCase


class PublicPagesTests(TestCase):
    """Các trang tĩnh không đụng tới database ngoài."""

    databases = {"default", "BB1"}

    @classmethod
    def setUpClass(cls) -> None:
        if not getattr(settings, "USE_SQLITE_FALLBACK", False):
            raise RuntimeError(
                "Chạy test với USE_SQLITE_FALLBACK=1 để tránh kết nối SQL Server."
            )
        super().setUpClass()

    def setUp(self) -> None:
        self.client = Client()

    def test_home(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BB", response.content)

    def test_about(self) -> None:
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)

    def test_kiemtratieuchuantheomay(self) -> None:
        response = self.client.get("/kiemtratieuchuantheomay")
        self.assertEqual(response.status_code, 200)

    def test_static_css_exists(self) -> None:
        self.assertTrue(
            os.path.exists(
                os.path.join(
                    settings.BASE_DIR,
                    "webhotroxuongBB",
                    "static",
                    "css",
                    "app.css",
                )
            )
        )
