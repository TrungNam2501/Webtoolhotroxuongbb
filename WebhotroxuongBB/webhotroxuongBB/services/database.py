"""Danh sách server + helper truy vấn nhiều DB BB cùng lúc."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class ServerStatus:
    """Kết quả query của 1 BB server — dùng để render card status."""

    server: str
    state: str  # "ok" | "nodata" | "error" | "scanned" | "not_scanned"
    message: str
    count: int = 0
    error: str = ""

    @property
    def short_label(self) -> str:
        if self.state == "ok":
            return "Có dữ liệu"
        if self.state == "nodata":
            return "Không có"
        if self.state == "scanned":
            return f"Đã quét {self.count} lần"
        if self.state == "not_scanned":
            return "Chưa quét"
        return "Lỗi kết nối"


def query_across_servers(
    servers: Iterable[str],
    model: type[Model],
    filter_field: str,
    query_value: str,
) -> tuple[list[Model] | Model | None, list[ServerStatus]]:
    """Truy vấn ``model`` trên nhiều database BB.

    - Nếu ``filter_field == 'mater_barcode'``: gom toàn bộ bản ghi khớp.
    - Ngược lại: chỉ trả về bản ghi đầu tiên tìm thấy.

    Trả về ``(result, statuses)``: mỗi ``ServerStatus`` mô tả trạng thái
    của 1 server (dùng để render card ở UI).
    """
    statuses: list[ServerStatus] = []

    if filter_field == "mater_barcode":
        result: list[Model] = []
        for server in servers:
            try:
                queryset = model.objects.using(server).filter(**{filter_field: query_value})
                count = queryset.count()
                if count:
                    result.extend(list(queryset))
                    statuses.append(
                        ServerStatus(
                            server=server,
                            state="scanned",
                            message=f"Máy {server} đã quét {count} lần",
                            count=count,
                        )
                    )
                else:
                    statuses.append(
                        ServerStatus(
                            server=server,
                            state="not_scanned",
                            message=f"Máy {server} chưa quét",
                        )
                    )
            except (OperationalError, DatabaseError) as exc:
                statuses.append(
                    ServerStatus(
                        server=server,
                        state="error",
                        message=f"Máy {server} tắt (lỗi kết nối)",
                        error=str(exc),
                    )
                )
        return result, statuses

    first_hit: Model | None = None
    for server in servers:
        try:
            obj = model.objects.using(server).filter(**{filter_field: query_value}).first()
            if obj:
                if first_hit is None:
                    first_hit = obj
                statuses.append(
                    ServerStatus(
                        server=server,
                        state="ok",
                        message=f"Máy {server} có dữ liệu",
                    )
                )
            else:
                statuses.append(
                    ServerStatus(
                        server=server,
                        state="nodata",
                        message=f"Máy {server} Nodata (quét hết, chưa mở, quá hạn, lỗi máy chưa có dữ liệu)",
                    )
                )
        except (OperationalError, DatabaseError) as exc:
            statuses.append(
                ServerStatus(
                    server=server,
                    state="error",
                    message=f"Máy {server} tắt (lỗi kết nối)",
                    error=str(exc),
                )
            )
    return first_hit, statuses
