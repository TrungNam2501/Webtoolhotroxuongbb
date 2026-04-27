import psycopg2
from psycopg2.extras import Json, RealDictCursor

# Định nghĩa SPECIAL_COLS
SPECIAL_COLS = {
    "kvmes.material_resource": {"jsonb": ["info"], "array": ["feed_records_id"]},
    "kvmes.collect_record": {"jsonb": ["detail"], "array": []},
    "kvmes.feed_record": {"jsonb": ["materials"], "array": []},
    "kvmes.batch": {"jsonb": ["records"], "array": ["records_id"]},
    "kvmes.work_order": {"jsonb": ["information"], "array": []}
}

def get_connection(db_config):
    """Tạo kết nối đến cơ sở dữ liệu."""
    return psycopg2.connect(
        host=db_config['HOST'],
        dbname=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        port=db_config['PORT'],
        options=db_config['OPTIONS']['options']
    )

def insert_data(conn, table, rows):
    """Chèn dữ liệu vào bảng với xử lý đặc biệt cho jsonb và array."""
    if not rows:
        return

    jsonb_cols = SPECIAL_COLS[table]["jsonb"]
    array_cols = SPECIAL_COLS[table]["array"]
    cols = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f"""
        INSERT INTO {table} ({", ".join(cols)})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
    """

    with conn.cursor() as cur:
        for row in rows:
            values = []
            for col in cols:
                val = row[col]
                if col in jsonb_cols:
                    values.append(Json(val))
                elif col in array_cols:
                    values.append(list(val) if val is not None else [])
                else:
                    values.append(val)
            cur.execute(sql, values)
    conn.commit()

def fetch_related_data(conn, material_id):
    """Lấy dữ liệu liên quan từ KV1KD dựa trên material_id."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 1. material_resource
        cur.execute("SELECT * FROM kvmes.material_resource WHERE id = %s", (material_id,))
        material_resource = cur.fetchall()

        # 2. collect_record
        cur.execute("""
            SELECT * FROM kvmes.collect_record
            WHERE resource_oid = (SELECT oid FROM kvmes.material_resource WHERE id = %s)
        """, (material_id,))
        collect_record = cur.fetchall()

        # 3. feed_record
        cur.execute("""
            SELECT * FROM kvmes.feed_record
            WHERE id = ANY(
                SELECT UNNEST(feed_records_id)
                FROM kvmes.material_resource
                WHERE id = %s
            )
        """, (material_id,))
        feed_record = cur.fetchall()

        # 4. batch
        cur.execute("""
            SELECT * FROM kvmes.batch
            WHERE records_id && (
                SELECT feed_records_id
                FROM kvmes.material_resource
                WHERE id = %s
            )
        """, (material_id,))
        batch = cur.fetchall()

        # 5. work_order
        cur.execute("""
            SELECT * FROM kvmes.work_order
            WHERE id = (
                SELECT work_order
                FROM kvmes.batch
                WHERE records_id && (
                    SELECT feed_records_id
                    FROM kvmes.material_resource
                    WHERE id = %s
                )
                LIMIT 1
            )
        """, (material_id,))
        work_order = cur.fetchall()

    return material_resource, collect_record, feed_record, batch, work_order