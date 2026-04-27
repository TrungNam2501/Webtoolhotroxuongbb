"""Views được chia nhỏ theo từng tool.

Re-export các view function để giữ nguyên đường dẫn import cũ
(``from webhotroxuongBB import views``).
"""

from .home import about, home, kiemtratieuchuantheomay
from .inlaitem import generate_excel, inlaitem
from .kiemtra import (
    insert_databaetembb,
    kiemtramokhoabb,
    kiemtratemquetbb,
)
from .tem_oem import temoembb
from .transfer import kv1tokv2, tembbcusangkd

__all__ = [
    "home",
    "about",
    "kiemtratieuchuantheomay",
    "inlaitem",
    "generate_excel",
    "kiemtratemquetbb",
    "kiemtramokhoabb",
    "insert_databaetembb",
    "temoembb",
    "kv1tokv2",
    "tembbcusangkd",
]
