"""Truy vấn tiêu chuẩn sản xuất trên các máy BB1–BB8.

- ``Ppt_GroupLot``: danh sách đơn làm trong ngày (cửa sổ 06:30 → 06:30).
- ``pmt_weigh``: các dòng cân nguyên liệu theo ``father_code``
  (thường là ``RecipeCode`` lấy từ ``Ppt_GroupLot``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from django.db import DatabaseError, OperationalError, connections


@dataclass
class GroupLotRow:
    id: int | None
    shift: str | None
    shift_class: str | None
    recipe_code: str | None
    recipe_name: str | None
    set_number: int | None
    start_datetime: datetime | None
    end_datetime: datetime | None
    finish_tag: str | None
    finish_num: int | None
    plan_id: str | None
    user_plan_id: str | None
    mes_plan_id: str | None


@dataclass
class PmtWeighRow:
    weight_id: Any
    father_code: str | None
    equip_code: str | None
    edt_code: str | None
    weigh_type: str | None
    act_code: str | None
    child_code: str | None
    child_name: str | None
    set_weight: Any
    error_allow: Any
    unit_name: str | None
    mem_note: str | None


GROUP_LOT_SQL = """
DECLARE @StartBoundary DATETIME;
DECLARE @EndBoundary DATETIME;

SET @StartBoundary = DATEADD(MINUTE, 390, CAST(CAST(GETDATE() AS DATE) AS DATETIME));
SET @EndBoundary = DATEADD(DAY, 1, @StartBoundary);

SELECT
    [Id], [Shift], [Shift_Class], [RecipeCode], [RecipeName], [SetNumber],
    [Start_datetime], [End_datetime], [FinishTag], [FinishNum],
    [Plan_ID], [UserPlanID], [MesPlanID]
FROM [mfns].[dbo].[Ppt_GroupLot]
WHERE [Start_datetime] >= @StartBoundary
  AND [Start_datetime] < @EndBoundary
ORDER BY [Start_datetime] DESC;
"""


PMT_WEIGH_SQL = """
SELECT TOP (1000)
    [weight_id], [father_code], [equip_code], [edt_code],
    [weigh_type], [act_code], [child_code], [child_name],
    [set_weight], [error_allow], [unit_name], [mem_note]
FROM [mfns].[dbo].[pmt_weigh]
WHERE father_code = %s
"""


class MachineUnreachable(RuntimeError):
    def __init__(self, machine: str, detail: str):
        super().__init__(f"Không kết nối được máy {machine}: {detail}")
        self.machine = machine
        self.detail = detail


def _rows(cursor, factory):
    cols = [c[0].lower() for c in cursor.description]
    rows = []
    for raw in cursor.fetchall():
        rows.append(factory(**{k: v for k, v in zip(cols, raw)}))
    return rows


def fetch_group_lot(machine: str) -> list[GroupLotRow]:
    """Danh sách đơn làm trong ngày trên 1 máy BB."""
    try:
        with connections[machine].cursor() as cur:
            cur.execute(GROUP_LOT_SQL)
            cols = [c[0].lower() for c in cur.description]
            mapping = {
                "id": "id",
                "shift": "shift",
                "shift_class": "shift_class",
                "recipecode": "recipe_code",
                "recipename": "recipe_name",
                "setnumber": "set_number",
                "start_datetime": "start_datetime",
                "end_datetime": "end_datetime",
                "finishtag": "finish_tag",
                "finishnum": "finish_num",
                "plan_id": "plan_id",
                "userplanid": "user_plan_id",
                "mesplanid": "mes_plan_id",
            }
            rows: list[GroupLotRow] = []
            for raw in cur.fetchall():
                kwargs = {
                    mapping.get(col, col): value
                    for col, value in zip(cols, raw)
                    if mapping.get(col, col) in GroupLotRow.__dataclass_fields__
                }
                for field in GroupLotRow.__dataclass_fields__:
                    kwargs.setdefault(field, None)
                rows.append(GroupLotRow(**kwargs))
            return rows
    except (OperationalError, DatabaseError) as exc:
        raise MachineUnreachable(machine, str(exc)) from exc


def fetch_pmt_weigh(machine: str, father_code: str) -> list[PmtWeighRow]:
    """Các dòng pmt_weigh khớp father_code trên 1 máy BB."""
    try:
        with connections[machine].cursor() as cur:
            cur.execute(PMT_WEIGH_SQL, [father_code])
            cols = [c[0].lower() for c in cur.description]
            rows: list[PmtWeighRow] = []
            for raw in cur.fetchall():
                kwargs = {col: value for col, value in zip(cols, raw)}
                for field in PmtWeighRow.__dataclass_fields__:
                    kwargs.setdefault(field, None)
                rows.append(PmtWeighRow(**{
                    k: v for k, v in kwargs.items()
                    if k in PmtWeighRow.__dataclass_fields__
                }))
            return rows
    except (OperationalError, DatabaseError) as exc:
        raise MachineUnreachable(machine, str(exc)) from exc


def row_to_dict(row: GroupLotRow | PmtWeighRow) -> dict[str, Any]:
    """Serialize cho JsonResponse (format datetime gọn gàng)."""
    data = asdict(row)
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.strftime("%Y-%m-%d %H:%M:%S")
    return data
