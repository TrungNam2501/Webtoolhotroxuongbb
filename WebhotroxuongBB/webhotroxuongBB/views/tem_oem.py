"""Trang quản lý tem OEM BB / hóa chất (IF_RtPlan2CWSS)."""

from __future__ import annotations

from django.contrib import messages as django_messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from ..services import tem_oem

BB_ACTIONS = {
    "one": (tem_oem.bb_insert_one, "success"),
    "all": (tem_oem.bb_insert_all, "info"),
    "delete": (tem_oem.bb_delete, "warning"),
}
CHEM_ACTIONS = {
    "import": (tem_oem.chem_update_oem, "success"),
    "delete": (tem_oem.chem_unupdate_oem, "warning"),
}


def _dispatch(request: HttpRequest, mapping: dict, action: str, tem_code: str) -> None:
    handler_ok_tag = mapping.get(action)
    if handler_ok_tag is None:
        return
    handler, ok_tag = handler_ok_tag
    success, msg_list = handler(tem_code)
    msg = msg_list[0] if msg_list else ""
    if success:
        add = getattr(django_messages, ok_tag, django_messages.info)
    else:
        add = django_messages.error
    add(request, msg)


def temoembb(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        tem_code = request.POST.get("tem_code", "").strip()
        action = request.POST.get("action", "")

        if form_type == "bb":
            _dispatch(request, BB_ACTIONS, action, tem_code)
        elif form_type == "hoa_chat":
            _dispatch(request, CHEM_ACTIONS, action, tem_code)

    return render(request, "temoembb.html")
