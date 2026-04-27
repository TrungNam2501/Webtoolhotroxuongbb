"""Trang chuyển dữ liệu giữa KV1/KV2 và từ BB cũ sang KD."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages as django_messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ..services.kv_sync import fetch_related_data, get_connection, insert_data
from ..services.transfer import run_transfer

logger = logging.getLogger(__name__)


def tembbcusangkd(request: HttpRequest) -> HttpResponse:
    where_clause = request.GET.get("where", "").strip()
    context = {"where": where_clause}

    if where_clause:
        try:
            inserted = run_transfer(where_clause)
            if inserted > 0:
                django_messages.success(request, f"✅ Đã chèn {inserted} bản ghi.")
            else:
                django_messages.warning(request, "⚠️ Không có bản ghi nào thỏa điều kiện.")
        except Exception as exc:  # noqa: BLE001
            django_messages.error(request, f"❌ Lỗi: {exc}")

    return render(request, "tembbcusangkd.html", context)


def kv1tokv2(request: HttpRequest) -> HttpResponse:
    """Sao chép material_resource + bảng liên quan từ KV1KD sang KV2KD."""
    context: dict = {}
    material_id = request.GET.get("barcode")
    context["barcode"] = material_id or ""

    if not material_id:
        return render(request, "kv1tokv2.html", context)

    conn_a = conn_b = None
    try:
        conn_a = get_connection(settings.DATABASES["KV1KD"])
        conn_b = get_connection(settings.DATABASES["KV2KD"])

        result = fetch_related_data(conn_a, material_id)
        if not result:
            django_messages.error(
                request, "Mã vạch chưa đúng hoặc không tồn tại trong KV1KD!"
            )
        else:
            mr, cr, fr, ba, wo = result
            if all(not x for x in (mr, cr, fr, ba, wo)):
                django_messages.error(
                    request, "Không tìm thấy dữ liệu trong KV1KD cho mã vạch này!"
                )
            else:
                inserted_tables: list[str] = []
                for table, data in (
                    ("kvmes.work_order", wo),
                    ("kvmes.material_resource", mr),
                    ("kvmes.feed_record", fr),
                    ("kvmes.batch", ba),
                    ("kvmes.collect_record", cr),
                ):
                    if data:
                        insert_data(conn_b, table, data)
                        inserted_tables.append(table.split(".")[-1])

                if inserted_tables:
                    django_messages.success(
                        request,
                        "Đã chèn dữ liệu vào các bảng: "
                        + ", ".join(inserted_tables),
                    )
                else:
                    django_messages.warning(
                        request, "Không có bảng nào được chèn dữ liệu!"
                    )
    except Exception as exc:  # noqa: BLE001
        django_messages.error(request, f"Lỗi: {exc}")
    finally:
        for conn in (conn_a, conn_b):
            try:
                if conn is not None:
                    conn.close()
            except Exception:  # noqa: BLE001
                logger.debug("Không thể đóng connection", exc_info=True)

    return render(request, "kv1tokv2.html", context)
