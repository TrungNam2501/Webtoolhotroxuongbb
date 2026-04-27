"""Trang 'Kiểm tra tiêu chuẩn theo máy'.

- ``GET /kiemtratieuchuantheomay?machine=BB1`` → danh sách đơn trong ngày.
- ``GET /kiemtratieuchuantheomay/weigh?machine=BB1&father_code=…``
  → JSON của pmt_weigh (dùng để fill modal sau khi bấm "Xem tiêu chuẩn").
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ..services.database import BB_SERVERS
from ..services.tieu_chuan import (
    MachineUnreachable,
    fetch_group_lot,
    fetch_pmt_weigh,
    row_to_dict,
)


def _pick_machine(request: HttpRequest) -> str:
    requested = (request.GET.get("machine") or "").strip()
    if requested in BB_SERVERS:
        return requested
    return BB_SERVERS[0]


@require_GET
def kiemtratieuchuantheomay(request: HttpRequest) -> HttpResponse:
    machine = _pick_machine(request)
    rows = []
    error_message = ""
    try:
        rows = fetch_group_lot(machine)
    except MachineUnreachable as exc:
        error_message = str(exc)

    return render(
        request,
        "kiemtratieuchuantheomay.html",
        {
            "machines": BB_SERVERS,
            "selected_machine": machine,
            "rows": rows,
            "error_message": error_message,
        },
    )


@require_GET
def kiemtratieuchuantheomay_weigh(request: HttpRequest) -> JsonResponse:
    machine = _pick_machine(request)
    father_code = (request.GET.get("father_code") or "").strip()
    if not father_code:
        return JsonResponse(
            {"success": False, "error": "Thiếu father_code."}, status=400
        )

    try:
        weighs = fetch_pmt_weigh(machine, father_code)
    except MachineUnreachable as exc:
        return JsonResponse(
            {"success": False, "error": str(exc), "machine": machine}, status=503
        )

    return JsonResponse(
        {
            "success": True,
            "machine": machine,
            "father_code": father_code,
            "rows": [row_to_dict(r) for r in weighs],
        }
    )
