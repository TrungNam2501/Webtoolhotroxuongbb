"""Các trang kiểm tra tem: scan BB, mở khóa BB, gia hạn, insert lại prdbae_temBB."""

from __future__ import annotations

import json
import logging

from django.db import DatabaseError, OperationalError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from ..models import (
    AutoSmallScanCode,
    IFMixPrintLab,
    Mes2RawMaterial,
    Prdbad,
    PptBarCodeRep,
    Prdbae,
    PrdbaeTemBB,
    Prdgdt,
)
from ..services.database import (
    BB_MFNS_SHARE_SERVERS,
    BB_SERVERS,
    query_across_servers,
)

logger = logging.getLogger(__name__)


def _merge_machine_status(
    data_statuses: list,
    scan_statuses: list,
) -> list[dict]:
    """Ghép cặp trạng thái dữ liệu / quét cho từng máy BB1..BB8.

    Tên server có thể là ``BB1`` hoặc ``BB1_mfnsshare``; chuẩn hóa về
    số thứ tự 1..8 để ghép 2 danh sách. Trả về list ``{name, data, scan}``.
    """

    def _machine_key(server: str) -> str:
        return server.split("_", 1)[0]  # "BB1_mfnsshare" -> "BB1"

    by_key = {_machine_key(s.server): s for s in data_statuses}
    scan_by_key = {_machine_key(s.server): s for s in scan_statuses}

    machines: list[dict] = []
    for index in range(1, len(BB_SERVERS) + 1):
        key = f"BB{index}"
        machines.append(
            {
                "name": key,
                "data": by_key.get(key),
                "scan": scan_by_key.get(key),
            }
        )
    return machines


def kiemtratemquetbb(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("barcode", "").strip()
    result = None
    result2: list = []
    machines: list[dict] = []
    error_message = ""

    if query:
        try:
            if query.startswith("V"):
                result, data_statuses = query_across_servers(
                    BB_SERVERS, AutoSmallScanCode, "plan_id", query
                )
            elif query.startswith("R"):
                result, data_statuses = query_across_servers(
                    BB_MFNS_SHARE_SERVERS, IFMixPrintLab, "barcode_lab", query
                )
            else:
                result, data_statuses = query_across_servers(
                    BB_SERVERS, Mes2RawMaterial, "barcode", query
                )

            result2, scan_statuses = query_across_servers(
                BB_SERVERS, PptBarCodeRep, "mater_barcode", query
            )

            machines = _merge_machine_status(data_statuses, scan_statuses)
        except (OperationalError, DatabaseError) as exc:
            error_message = f"Lỗi cơ sở dữ liệu: {exc}"
            result = []
        except Exception as exc:  # noqa: BLE001
            error_message = f"Lỗi hệ thống không xác định: {exc}"
            result = []

    return render(
        request,
        "kiemtratemquetbb.html",
        {
            "query": query,
            "result": result,
            "result2": result2,
            "machines": machines,
            "error_message": error_message,
        },
    )


def kiemtramokhoabb(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("barcode", "").strip()
    result = None

    if query:
        try:
            if len(query) > 10:
                result = Prdgdt.objects.filter(slipno=query).first()
            else:
                result = Prdbae.objects.filter(slipno=query).order_by("-id").first()

            if result is not None:
                if getattr(result, "reason", None):
                    result.reason = result.reason.strip()
                if getattr(result, "slipno", None):
                    result.slipno = result.slipno.strip()
        except (Prdbae.DoesNotExist, Prdgdt.DoesNotExist):
            result = None

    return render(request, "kiemtramokhoabb.html", {"query": query, "result": result})


@csrf_exempt  # chỉ dùng trong phát triển — nên bảo vệ bằng auth khi lên prod
def insert_databaetembb(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"message": "Yêu cầu không hợp lệ!"}, status=400)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"message": "JSON không hợp lệ"}, status=400)

    PrdbaeTemBB(
        subno=data.get("subno", ""),
        slipno=data.get("slipno", ""),
        stacode=data.get("stacode", ""),
        reason=data.get("reason", ""),
        indat=data.get("indat", ""),
        intime=data.get("intime", ""),
        usrno=data.get("usrno", ""),
    ).save()
    return JsonResponse({"message": "Dữ liệu đã được chèn thành công!"}, status=201)


def kiemtragiahan(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("barcode", "").strip()
    results = []
    error_message = ""
    searched = False

    if query:
        searched = True
        if not query.startswith("R"):
            error_message = "Barcode phải bắt đầu bằng ký tự 'R'."
        else:
            try:
                results = list(
                    Prdbad.objects.using("default")
                    .filter(slipno__startswith=query, mark="Y")
                    .exclude(slipno__startswith="RD")
                    .order_by("-id")
                )
                for row in results:
                    if row.slipno:
                        row.slipno = row.slipno.strip()
                    if row.stacodena:
                        row.stacodena = row.stacodena.strip()
                    if row.dutydeptna:
                        row.dutydeptna = row.dutydeptna.strip()
                    if row.usrno:
                        row.usrno = row.usrno.strip()
            except (OperationalError, DatabaseError) as exc:
                error_message = f"Lỗi cơ sở dữ liệu: {exc}"
            except Exception as exc:  # noqa: BLE001
                error_message = f"Lỗi hệ thống: {exc}"

    return render(
        request,
        "kiemtragiahan.html",
        {
            "query": query,
            "results": results,
            "total_results": len(results),
            "searched": searched,
            "error_message": error_message,
        },
    )
