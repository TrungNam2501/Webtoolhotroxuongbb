"""Danh sách server + helper truy vấn nhiều DB BB cùng lúc."""

from __future__ import annotations

from typing import Iterable

from django.db import DatabaseError, OperationalError
from django.db.models import Model

BB_SERVERS: list[str] = ["BB1", "BB2", "BB3", "BB4", "BB5", "BB6", "BB7", "BB8"]
BB_MFNS_SHARE_SERVERS: list[str] = [f"{name}_mfnsshare" for name in BB_SERVERS]

PRINTERS: list[str] = [
    "HL-L2360D 8.122",
    "HL-L2360D 9.176",
    "HL-L2360D 9.193",
    "HL-L2360D 4.140",
]


def query_across_servers(
    servers: Iterable[str],
    model: type[Model],
    filter_field: str,
    query_value: str,
) -> tuple[list[Model] | Model | None, list[str]]:
    """Truy vấn ``model`` trên nhiều database BB.

    - Nếu ``filter_field == 'mater_barcode'``: gom toàn bộ bản ghi khớp.
    - Ngược lại: chỉ trả về bản ghi đầu tiên tìm thấy.
    """
    messages: list[str] = []

    if filter_field == "mater_barcode":
        result: list[Model] = []
        for server in servers:
            try:
                queryset = model.objects.using(server).filter(**{filter_field: query_value})
                count = queryset.count()
                if count:
                    result.extend(list(queryset))
                    messages.append(f"Máy {server} đã quét {count} lần")
                else:
                    messages.append(f"Máy {server} chưa quét")
            except (OperationalError, DatabaseError) as exc:
                messages.append(f"Máy {server} tắt (lỗi kết nối: {exc})")
        if not result:
            messages.append("Không tìm thấy dữ liệu ở máy nào")
        return result, messages

    first_hit: Model | None = None
    for server in servers:
        try:
            obj = model.objects.using(server).filter(**{filter_field: query_value}).first()
            if obj:
                if first_hit is None:
                    first_hit = obj
                messages.append(f"Máy {server} có dữ liệu")
            else:
                messages.append(
                    f"Máy {server} Nodata (quét hết, chưa mở, quá hạn, lỗi máy chưa có dữ liệu)"
                )
        except (OperationalError, DatabaseError) as exc:
            messages.append(f"Máy {server} tắt (lỗi kết nối: {exc})")
    return first_hit, messages
