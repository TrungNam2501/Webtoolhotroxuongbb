"""Các trang tĩnh: trang chủ, giới thiệu, placeholder tiêu chuẩn."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

TOOLS = [
    {
        "title": "In lại tem",
        "description": "Tra cứu barcode/pallet và in lại tem BB.",
        "url": "/inlaitem",
        "icon": "printer",
        "accent": "primary",
    },
    {
        "title": "KV1 → KV2",
        "description": "Đồng bộ material_resource / batch / work_order qua KV2.",
        "url": "/kv1tokv2",
        "icon": "sync",
        "accent": "teal",
    },
    {
        "title": "Tem BB cũ → KD",
        "description": "Chuyển dữ liệu prdebe sang kvmes.material_resource.",
        "url": "/tembbcusangkd",
        "icon": "shuffle",
        "accent": "violet",
    },
    {
        "title": "Kiểm tem scan BB",
        "description": "Quét các máy BB1..BB8 theo barcode.",
        "url": "/kiemtratemquetbb",
        "icon": "scan",
        "accent": "sky",
    },
    {
        "title": "Kiểm tem mở khóa BB",
        "description": "Tra slipno ở prdgdt/prdbae và chuyển lại khi cần.",
        "url": "/kiemtramokhoabb",
        "icon": "lock",
        "accent": "amber",
    },
    {
        "title": "Tem OEM BB",
        "description": "Insert/Delete TemOEMBB, update/unupdate IF_RtPlan2CWSS.",
        "url": "/temoembb",
        "icon": "tag",
        "accent": "emerald",
    },
    {
        "title": "Kiểm tiêu chuẩn máy",
        "description": "Sắp có: tiêu chuẩn kỹ thuật theo máy trộn.",
        "url": "/kiemtratieuchuantheomay",
        "icon": "ruler",
        "accent": "slate",
    },
    {
        "title": "Giới thiệu",
        "description": "Về phòng Vi Tính KV2.",
        "url": "/about",
        "icon": "info",
        "accent": "slate",
    },
]


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html", {"tools": TOOLS})


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html")


def kiemtratieuchuantheomay(request: HttpRequest) -> HttpResponse:
    return render(request, "kiemtratieuchuantheomay.html")
