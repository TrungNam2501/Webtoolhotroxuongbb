"""Views được chia nhỏ theo từng tool.

Re-export các view function để giữ nguyên đường dẫn import cũ
(``from webhotroxuongBB import views``).
"""

from .home import about, home
from .inlaitem import generate_excel, inlaitem
from .kiemtra import (
    insert_databaetembb,
    kiemtragiahan,
    kiemtragiahan_update,
    kiemtramokhoabb,
    kiemtratemquetbb,
    mothemtemquetbb,
)
from .tem_oem import temoembb
from .tieu_chuan import kiemtratieuchuantheomay, kiemtratieuchuantheomay_weigh
from .transfer import kv1tokv2, tembbcusangkd

__all__ = [
    "home",
    "about",
    "kiemtratieuchuantheomay",
    "kiemtratieuchuantheomay_weigh",
    "inlaitem",
    "generate_excel",
    "kiemtratemquetbb",
    "kiemtramokhoabb",
    "insert_databaetembb",
    "kiemtragiahan",
    "kiemtragiahan_update",
    "mothemtemquetbb",
    "temoembb",
    "kv1tokv2",
    "tembbcusangkd",
]
