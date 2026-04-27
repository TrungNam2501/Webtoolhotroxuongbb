"""Các trang kiểm tra tem: scan BB, mở khóa BB, insert lại prdbae_temBB."""

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


def kiemtratemquetbb(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("barcode", "").strip()
    result = None
    result2: list = []
    summary = ""
    summary2 = ""

    if query:
        try:
            if query.startswith("V"):
                result, messages = query_across_servers(
                    BB_SERVERS, AutoSmallScanCode, "plan_id", query
                )
            elif query.startswith("R"):
                result, messages = query_across_servers(
                    BB_MFNS_SHARE_SERVERS, IFMixPrintLab, "barcode_lab", query
                )
            else:
                result, messages = query_across_servers(
                    BB_SERVERS, Mes2RawMaterial, "barcode", query
                )

            result2, messages2 = query_across_servers(
                BB_SERVERS, PptBarCodeRep, "mater_barcode", query
            )

            summary = ", ".join(messages)
            summary2 = (
                f", {messages2}"
                if isinstance(messages2, str)
                else f" {', '.join(messages2)}"
            )
        except (OperationalError, DatabaseError) as exc:
            summary = f"Lỗi cơ sở dữ liệu: {exc}"
            result = []
        except Exception as exc:  # noqa: BLE001
            summary = f"Lỗi hệ thống không xác định: {exc}"
            result = []

    return render(
        request,
        "kiemtratemquetbb.html",
        {
            "query": query,
            "result": result,
            "result2": result2,
            "summary": summary,
            "summary2": summary2,
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
