"""Trang "In lại tem" và endpoint generate_excel."""

from __future__ import annotations

import logging
import os
from typing import Any

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from ..models import Prdebe
from ..services.database import PRINTERS
from ..services.excel import GetExcelInlaiBB
from ..services.printer import PrinterUnavailable, print_excel_to

logger = logging.getLogger(__name__)

PAGE_SIZE = 20


def _clean(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def inlaitem(request: HttpRequest) -> HttpResponse:
    barcode = request.GET.get("barcode", "").strip()
    results = []

    if barcode:
        if len(barcode) > 7:
            results = Prdebe.objects.filter(barcode=barcode).order_by("-indat", "-intime")
        else:
            results = Prdebe.objects.filter(pallet_no=barcode).order_by("-indat", "-intime")

    total_results = results.count() if results else 0
    page_obj = None
    results_to_display: Any = results
    if total_results > PAGE_SIZE:
        paginator = Paginator(results, PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page"))
        results_to_display = page_obj

    return render(
        request,
        "inlaitem.html",
        {
            "query": barcode,
            "results": results_to_display,
            "page_obj": page_obj,
            "total_results": total_results,
            "printers": PRINTERS,
        },
    )


def _lookup_oem_flag(barcode: str) -> str:
    """Kiểm tra nhanh bản ghi barcode có phải OEM không (SQL Server 10.33)."""
    try:
        import pyodbc  # lazy import, tránh hỏng app khi driver chưa có
    except ImportError:
        logger.warning("pyodbc chưa cài — bỏ qua kiểm OEM.")
        return ""

    from django.conf import settings

    bb_cfg = settings.DATABASES.get("33BB", {})
    driver = bb_cfg.get("OPTIONS", {}).get("driver", "SQL Server")
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={bb_cfg.get('HOST', '198.1.10.33')};"
        f"DATABASE={bb_cfg.get('NAME', 'BB')};"
        f"UID={bb_cfg.get('USER', '')};"
        f"PWD={bb_cfg.get('PASSWORD', '')}"
    )
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Barcode FROM dbo.TemOEMBB WHERE Barcode = ?", barcode)
            if cursor.fetchone():
                return "OEM"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lỗi kết nối BB khi kiểm OEM: %s", exc)
    return ""


def generate_excel(request: HttpRequest) -> JsonResponse:
    barcode = request.GET.get("barcode", "").strip()
    printer_name = request.GET.get("printer", "").strip()

    if not barcode or not printer_name:
        return JsonResponse({"success": False, "error": "Thiếu barcode hoặc máy in"})

    if len(barcode) > 7:
        data = Prdebe.objects.filter(barcode=barcode).order_by("-indat", "-intime")
    else:
        data = Prdebe.objects.filter(pallet_no=barcode).order_by("-indat", "-intime")

    if not data.exists():
        return JsonResponse({"success": False, "error": "Không tìm thấy dữ liệu"})

    row = data.first()
    description = _lookup_oem_flag(row.barcode)

    tmp_folder = os.path.join(os.path.dirname(__file__), "..", "services", "temp")
    tmp_folder = os.path.abspath(tmp_folder)
    os.makedirs(tmp_folder, exist_ok=True)
    tmp_file_path = os.path.join(tmp_folder, f"{barcode}.xlsx")

    excel_path = GetExcelInlaiBB.create_excel(
        partno=_clean(row.partno),
        effdat=row.effdat,
        path_file=tmp_file_path,
        slipno=_clean(row.slipno),
        barcode=_clean(row.barcode),
        ca=_clean(row.pclass),
        daylimt=row.daylimt,
        soluong=row.weight,
        mesid=_clean(row.mesid),
        machno=_clean(row.machno),
        pday=row.prodat,
        indat=row.indat,
        classs=_clean(row.pclass),
        intime=row.intime,
        pallet=_clean(row.pallet_no),
        loaikeo=_clean(row.barcode)[:2] if row.barcode else "",
        description=_clean(description),
        masosx=row.some_sx,
    )

    if isinstance(excel_path, str) and "Lỗi" in excel_path:
        return JsonResponse({"success": False, "error": excel_path})

    try:
        print_excel_to(printer_name, excel_path)
    except PrinterUnavailable as exc:
        return JsonResponse({"success": False, "error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"success": False, "error": str(exc)})

    return JsonResponse({"success": True, "message": "Đã gửi lệnh in thành công"})
