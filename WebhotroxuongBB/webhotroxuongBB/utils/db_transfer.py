import pyodbc
import psycopg2
import uuid
import json
from datetime import datetime, time as dtime
import pytz
from django.conf import settings


def get_connection(db_config):
    """Tạo kết nối đến cơ sở dữ liệu."""
    if db_config['ENGINE'] == 'mssql':
        # SQL Server connection using pyodbc
        conn_str = (
            f"DRIVER={{{db_config['OPTIONS']['driver']}}};"
            f"SERVER={db_config['HOST']};"
            f"DATABASE={db_config['NAME']};"
            f"UID={db_config['USER']};"
            f"PWD={db_config['PASSWORD']};"
            f"{db_config['OPTIONS'].get('extra_params', '')}"
        )
        return pyodbc.connect(conn_str)
    else:
        # PostgreSQL connection using psycopg2
        return psycopg2.connect(
            host=db_config['HOST'],
            dbname=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            port=db_config['PORT'],
            options=db_config.get('OPTIONS', {}).get('options', '')
        )


def run_transfer(where_clause: str) -> int:
    """
    Chuyển dữ liệu từ [erp].[dbo].[prdebe] (SQL Server) sang kvmes.material_resource (PostgreSQL)
    theo điều kiện WHERE thô (vd: "barcode LIKE 'ABC%'").
    Trả về số bản ghi đã cố gắng chèn (bản trùng id+product_id sẽ bị ON CONFLICT bỏ qua).
    Ném Exception để view hiển thị messages.
    """
    if not where_clause or not where_clause.strip():
        return 0

    sql_server_conn = sql_cursor = None
    pg_conn = pg_cursor = None
    try:
        # --- Kết nối ---
        sql_server_conn = get_connection(settings.DATABASES['default'])
        sql_cursor = sql_server_conn.cursor()

        pg_conn = get_connection(settings.DATABASES['KV2KD'])
        pg_cursor = pg_conn.cursor()

        # --- Lấy dữ liệu: chỉ định cột cần thiết ---
        query = f"""
            SELECT barcode, partno, weight, effdat, indat, intime, usrno
            FROM [erp].[dbo].[prdebe]
            WHERE {where_clause}
        """
        sql_cursor.execute(query)
        rows = sql_cursor.fetchall()

        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")

        def _to_ns_epoch(dt_utc: datetime) -> int:
            return int(dt_utc.timestamp()) * 1_000_000_000

        def _eod_vn_to_utc_ns(yyyymmdd) -> int:
            # cuối ngày VN 23:59:59 → UTC → ns
            d = datetime.strptime(str(yyyymmdd).strip(), "%Y%m%d").date()
            dt_vn = vn_tz.localize(datetime.combine(d, dtime(23, 59, 59)))
            return _to_ns_epoch(dt_vn.astimezone(pytz.utc))

        def _combine_vn_to_utc(indat, intime) -> datetime:
            # chấp nhận 'HH:MM:SS' hoặc 'HHMMSS'
            tstr = str(intime)
            if ":" not in tstr:
                tstr = tstr.zfill(6)
                tstr = f"{tstr[0:2]}:{tstr[2:4]}:{tstr[4:6]}"
            d = datetime.strptime(str(indat), "%Y%m%d").date()
            t = datetime.strptime(tstr, "%H:%M:%S").time()
            dt_vn = vn_tz.localize(datetime.combine(d, t))
            return dt_vn.astimezone(pytz.utc)

        insert_sql = """
        INSERT INTO kvmes.material_resource (
            oid, id, product_id, product_type, quantity, status,
            expiry_time, info, warehouse_id, warehouse_location,
            updated_at, updated_by, created_at, created_by,
            station, feed_records_id, batch_count, reprint_reason,
            collected, erp_tire_barcode_synced, standing_time
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s::jsonb, %s, %s,
            %s, %s, %s, %s,
            %s, %s::text[], %s, %s,
            %s, %s, %s
        )
        ON CONFLICT (id, product_id) DO NOTHING
        """

        inserted_try = 0
        for row in rows:
            oid = str(uuid.uuid4())
            id_val = (row.barcode or "").strip()
            product_id = (row.partno or "").strip()
            product_type = "RUBBER"
            quantity = float(row.weight) if row.weight is not None else 0.0
            status = 1

            # expiry_time (ns)
            try:
                expiry_time = _eod_vn_to_utc_ns(row.effdat)
            except Exception:
                expiry_time = 0

            # production_time & *_at (ns)
            try:
                dt_utc = _combine_vn_to_utc(row.indat, row.intime)
            except Exception:
                dt_utc = datetime.now(pytz.utc)

            production_time = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            ts_ns = _to_ns_epoch(dt_utc)

            updated_at = created_at = standing_time = ts_ns
            updated_by = created_by = str(getattr(row, "usrno", "") or "")

            info = json.dumps({
                "unit": "",
                "grade": "",
                "remark": "",
                "change_log": [],
                "lot_number": "",
                "min_dosage": "0",
                "hold_reason": 0,
                "inspections": [],
                "deferrals_count": 0,
                "production_info": {
                    "station": "",
                    "recipe_id": "",
                    "next_station": "",
                    "process_name": "",
                    "process_type": "",
                    "production_time": production_time
                },
                "planned_quantity": "0",
                "additional_fields": None
            })

            # feed_records_id là text[] -> truyền list [] và ép ::text[]
            pg_cursor.execute(insert_sql, (
                oid, id_val, product_id, product_type, quantity, status,
                expiry_time, info, '', '',
                updated_at, updated_by, created_at, created_by,
                '', [], 0, 0, False, False, standing_time
            ))
            inserted_try += 1

        pg_conn.commit()
        return inserted_try

    except Exception as e:
        if pg_conn:
            pg_conn.rollback()
        # ném lỗi để view bắt và hiển thị messages
        raise
    finally:
        try:
            if sql_cursor:
                sql_cursor.close()
        except:
            pass
        try:
            if sql_server_conn:
                sql_server_conn.close()
        except:
            pass
        try:
            if pg_cursor:
                pg_cursor.close()
        except:
            pass
        try:
            if pg_conn:
                pg_conn.close()
        except:
            pass