# Webtoolhotroxuongbb

Hệ thống web nội bộ hỗ trợ phân xưởng BB của Công ty Cao su Kenda Việt Nam.
Ứng dụng được xây dựng trên **Django 5.2** và kết nối tới nhiều instance
SQL Server (máy trộn BB1–BB8, ERP 10.33) cùng PostgreSQL (KV1KD / KV2KD).

## Cấu trúc thư mục

```
Webtoolhotroxuongbb/
├── .env.example              # Mẫu file cấu hình môi trường
├── .gitignore
├── README.md
└── WebhotroxuongBB/
    ├── manage.py
    ├── requirements.txt
    ├── config/                       # Django project settings
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    └── webhotroxuongBB/              # Ứng dụng chính
        ├── apps.py
        ├── admin.py
        ├── models.py
        ├── urls.py
        ├── views/                    # Views được chia theo chức năng
        │   ├── __init__.py
        │   ├── home.py
        │   ├── inlaitem.py
        │   ├── kiemtra.py
        │   ├── tem_oem.py
        │   └── transfer.py
        ├── services/                 # Logic nghiệp vụ, kết nối DB, in ấn
        │   ├── __init__.py
        │   ├── database.py           # Constants server BB1..BB8
        │   ├── tem_oem.py
        │   ├── transfer.py
        │   ├── kv_sync.py
        │   ├── printer.py            # Bọc win32 (tùy chọn)
        │   └── excel.py
        ├── static/
        │   ├── css/app.css           # Stylesheet dùng chung
        │   └── logo/
        ├── templates/                # Template có chung base.html
        └── tests.py
```

## Yêu cầu

- Python 3.12 – 3.14
- Driver `ODBC Driver 18 for SQL Server` (trên máy kết nối SQL Server thật)
- Máy production Windows nếu cần in tem qua `win32print`; môi trường dev/CI
  không cần cài `pywin32`.

## Cài đặt nhanh (development)

```bash
git clone https://github.com/TrungNam2501/Webtoolhotroxuongbb.git
cd Webtoolhotroxuongbb/WebhotroxuongBB

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example .env      # điền thông tin phù hợp
python manage.py check
python manage.py runserver
```

### Chạy thử không cần SQL Server

Khi chưa có quyền truy cập SQL Server / PostgreSQL nội bộ, đặt
`USE_SQLITE_FALLBACK=1` trong `.env` để Django dùng SQLite cho `default`
nhằm phục vụ kiểm tra cấu hình:

```bash
export USE_SQLITE_FALLBACK=1
python manage.py check
python manage.py migrate
python manage.py runserver
```

Các view kết nối SQL Server/PG sẽ báo lỗi khi không có DNS/mạng nội bộ,
nhưng trang chủ, trang giới thiệu và khung giao diện vẫn hoạt động.

## Biến môi trường

Xem `.env.example`. Các biến chính:

| Nhóm          | Biến                                               |
|---------------|----------------------------------------------------|
| Django        | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` |
| Fallback      | `USE_SQLITE_FALLBACK`                              |
| MSSQL chung   | `MSSQL_USER`, `MSSQL_PASSWORD`                     |
| MSSQL hosts   | `MSSQL_ERP_HOST`, `MSSQL_BB_HOST`, `MSSQL_BB<N>_HOST` (N = 1..8) |
| PostgreSQL    | `PG_USER`, `PG_PASSWORD`, `PG_KV1KD_HOST`, `PG_KV2KD_HOST` |

## Các tool hiện có

- **Trang chủ (/)**: Dashboard giới thiệu tool.
- **In lại tem (/inlaitem)**: tra Prdebe theo barcode/pallet, chọn máy in
  và gửi lệnh in Excel.
- **KV1 → KV2 (/kv1tokv2)**: đồng bộ material_resource / collect_record /
  feed_record / batch / work_order giữa 2 database Postgres.
- **Tem BB cũ sang KD (/tembbcusangkd)**: chuyển dữ liệu từ `erp.prdebe`
  sang `kvmes.material_resource` theo điều kiện WHERE.
- **Kiểm tra tem scan BB (/kiemtratemquetbb)**: quét nhiều server BB theo
  prefix barcode (`V…`, `R…`, số).
- **Kiểm tra tem mở khóa BB (/kiemtramokhoabb)**: tra `prdgdt`/`prdbae`
  theo slipno và cho phép chuyển lại.
- **Tem OEM BB (/temoembb)**: quản lý `TemOEMBB`, `IF_RtPlan2CWSS`
  (insert/delete theo mesid, update/unupdate OEM theo plan_id).
- **Kiểm tiêu chuẩn theo máy (/kiemtratieuchuantheomay)**: placeholder.
- **Giới thiệu (/about)**: thông tin phòng Vi Tính KV2.

## Phát triển

```bash
python manage.py check
python manage.py collectstatic --noinput --dry-run
python manage.py test
```

## Đóng gói / triển khai

- Thiết lập các biến môi trường ở trên.
- Chạy `python manage.py collectstatic --noinput` rồi dùng
  WSGI server (gunicorn/uwsgi trên Linux hoặc IIS + wfastcgi trên Windows).
