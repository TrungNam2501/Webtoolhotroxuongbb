"""Service xử lý tem OEM BB và tem hóa chất (IF_RtPlan2CWSS)."""

from __future__ import annotations

from django.utils import timezone

from ..models import Prdebe, RtPlan2CWSS, TemOEMBB

SOURCE_DB = "default"
TARGET_DB = "33BB"


def bb_insert_one(tem_code: str) -> tuple[bool, list[str]]:
    """Thêm 1 tem OEM (TemOEMBB) dựa vào bản ghi prdebe."""
    try:
        if TemOEMBB.objects.using(TARGET_DB).filter(barcode=tem_code).exists():
            return False, [f"Bảng TemOEMBB 10.33 db:BB. Tem {tem_code} đã có rồi."]

        source = Prdebe.objects.using(SOURCE_DB).filter(barcode=tem_code).first()
        if not source:
            return False, [
                f"Lỗi: Không thấy tem {tem_code} ở table prdebe 10.33 db:erp "
                "(Nhập tem sai rồi)"
            ]

        now = timezone.now()
        TemOEMBB.objects.using(TARGET_DB).create(
            barcode=source.barcode,
            mesid=source.mesid,
            partno=source.partno,
            indat=now.strftime("%Y%m%d"),
            intime=now.strftime("%H:%M:%S"),
        )
        return True, [f"Bảng TemOEMBB 10.33 db:BB. Thêm thành công tem {tem_code}"]
    except Exception as exc:  # noqa: BLE001 - expose message to UI
        return False, [f"Lỗi hệ thống: {exc}"]


def bb_insert_all(tem_code: str) -> tuple[bool, list[str]]:
    """Insert toàn bộ tem cùng ``mesid`` với ``tem_code`` (bỏ qua tem đã có)."""
    try:
        root = Prdebe.objects.using(SOURCE_DB).filter(barcode=tem_code).first()
        if not root:
            return False, [
                f"Lỗi: Không thấy tem {tem_code} ở table prdebe 10.33 db:erp "
                "(Nhập tem sai rồi)"
            ]

        target_mesid = root.mesid
        group = Prdebe.objects.using(SOURCE_DB).filter(mesid=target_mesid)

        now = timezone.now()
        current_date = now.strftime("%Y%m%d")
        current_time = now.strftime("%H:%M:%S")

        inserted = skipped = 0
        for item in group:
            exists = (
                TemOEMBB.objects.using(TARGET_DB)
                .filter(barcode=item.barcode)
                .exists()
            )
            if exists:
                skipped += 1
                continue
            TemOEMBB.objects.using(TARGET_DB).create(
                barcode=item.barcode,
                mesid=item.mesid,
                partno=item.partno,
                indat=current_date,
                intime=current_time,
            )
            inserted += 1

        message = (
            f"MESID: {target_mesid} | Tổng nhóm: {group.count()} tem. "
            f"Đã thêm mới: {inserted}, Đã bỏ qua (trùng): {skipped}"
        )
        return True, [message]
    except Exception as exc:  # noqa: BLE001
        return False, [f"Lỗi hệ thống: {exc}"]


def bb_delete(tem_code: str) -> tuple[bool, list[str]]:
    """Xóa toàn bộ tem cùng ``mesid`` với ``tem_code`` trong TemOEMBB."""
    try:
        root = Prdebe.objects.using(SOURCE_DB).filter(barcode=tem_code).first()
        if not root:
            return False, [
                f"Lỗi: Không thấy tem {tem_code} ở table prdebe 10.33 db:erp "
                "(Nhập tem sai rồi)"
            ]

        target_mesid = root.mesid
        barcodes = list(
            Prdebe.objects.using(SOURCE_DB)
            .filter(mesid=target_mesid)
            .values_list("barcode", flat=True)
        )
        if not barcodes:
            return True, [f"MESID {target_mesid}: Nhóm này không có mã vạch nào."]

        deleted, _ = (
            TemOEMBB.objects.using(TARGET_DB)
            .filter(barcode__in=barcodes)
            .delete()
        )
        if deleted > 0:
            return True, [
                f"MESID {target_mesid}: Đã xóa thành công {deleted} tem tại "
                "TemOEMBB 10.33 db:BB."
            ]
        return True, [
            f"MESID {target_mesid}: Không tìm thấy tem nào để xóa tại "
            "TemOEMBB 10.33 db:BB."
        ]
    except Exception as exc:  # noqa: BLE001
        return False, [f"Lỗi hệ thống: {exc}"]


def chem_update_oem(tem_code: str) -> tuple[bool, list[str]]:
    """Gắn cờ ``OEM`` cho các dòng khớp ``plan_id`` ở IF_RtPlan2CWSS."""
    try:
        queryset = RtPlan2CWSS.objects.using(TARGET_DB).filter(plan_id=tem_code)
        if not queryset.exists():
            return False, [
                f"Mã Plan ID {tem_code} không tồn tại trên bảng "
                "'IF_RtPlan2CWSS' (DB: 10.33)."
            ]
        needs_update = queryset.exclude(oem="OEM")
        if not needs_update.exists():
            return False, [
                f"Mã Plan ID {tem_code} đã được cập nhật 'OEM' từ trước rồi."
            ]
        updated = needs_update.update(oem="OEM")
        return True, [
            f"Đã cập nhật thành công 'OEM' cho {updated} dòng của Plan ID {tem_code}."
        ]
    except Exception as exc:  # noqa: BLE001
        return False, [f"Lỗi hệ thống update hóa chất: {exc}"]


def chem_unupdate_oem(tem_code: str) -> tuple[bool, list[str]]:
    """Đưa các dòng ``plan_id`` về trạng thái ``KD`` ở IF_RtPlan2CWSS."""
    try:
        queryset = RtPlan2CWSS.objects.using(TARGET_DB).filter(plan_id=tem_code)
        if not queryset.exists():
            return False, [
                f"Mã Plan ID {tem_code} không tồn tại trên bảng "
                "'IF_RtPlan2CWSS' (DB: 10.33)."
            ]
        needs_revert = queryset.exclude(oem="KD")
        if not needs_revert.exists():
            return False, [
                f"Mã Plan ID {tem_code} hiện đã ở trạng thái thường (KD) rồi, "
                "không cần hoàn tác."
            ]
        updated = needs_revert.update(oem="KD")
        return True, [
            "Đã cập nhật thành công về trạng thái thường (KD) cho "
            f"{updated} dòng của Plan ID {tem_code}."
        ]
    except Exception as exc:  # noqa: BLE001
        return False, [f"Lỗi hệ thống hoàn tác hóa chất: {exc}"]
