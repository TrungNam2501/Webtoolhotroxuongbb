from django.shortcuts import render





from .utils.excel_utils import GetExcelInlaiBB
from .utils.temoem import TemOEMHandler
from .utils.kv1tokv2 import get_connection, insert_data, fetch_related_data
from .utils.db_transfer import run_transfer

from django.core.paginator import Paginator
# Create your views here.
from .models import Prdebe
from .models import Prdbae
from .models import Prdgdt
from .models import PrdbaeTemBB

from .models import Mes2RawMaterial
from .models import AutoSmallScanCode
from .models import IFMixPrintLab
from .models import PptBarCodeRep


from django.http import JsonResponse
import openpyxl
import tempfile
import os
import win32print
import win32api
import pyodbc 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import OperationalError, DatabaseError
from django.contrib import messages
from django.conf import settings

def home(request):
    return render(request, 'home.html')
def about(request):
    return render(request, 'about.html')

def kiemtratieuchuantheomay(request):
    return render(request, 'kiemtratieuchuantheomay.html')


def temoembb(request):
    handler = TemOEMHandler() 

    if request.method == "POST":
        form_type = request.POST.get('form_type')
        tem_code = request.POST.get('tem_code')
        action = request.POST.get('action')

        # Xử lý cụm BB
        if form_type == "bb":
            if action == "one":
                # SỬA Ở ĐÂY: Nhận về 2 giá trị (status và msg_list)
                success, msg_list = handler.bb_insert_one(tem_code)
                
                if success:
                    # Vì msg_list là một danh sách ['...'], ta lấy phần tử đầu tiên [0]
                    messages.success(request, msg_list[0])
                else:
                    # Nếu thất bại (trả về False), hiển thị lỗi từ msg_list
                    messages.error(request, msg_list[0])

            elif action == "all":
                # Tương tự cho các hàm khác nếu chúng cũng trả về tuple (True/False, List)
                success, msg_list = handler.bb_insert_all(tem_code)
                if success:
                    messages.info(request, msg_list[0])
                else:
                    messages.error(request, msg_list[0])

            elif action == "delete":
                success, msg_list = handler.bb_delete(tem_code)
                if success:
                    messages.warning(request, msg_list[0])
                else:
                    messages.error(request, msg_list[0])

        # Xử lý cụm Hóa chất (Làm tương tự nếu handler.chem_insert trả về tuple)
        elif form_type == "hoa_chat":
            if action == "import":
                success, msg_list = handler.chem_updateoem(tem_code)
                if success:
                    messages.success(request, msg_list[0])
                else:
                    messages.error(request, msg_list[0])
                    
            elif action == "delete":
                # SỬA TẠI ĐÂY: Gọi hàm chem_delete thay vì chem_insert
                success, msg_list = handler.chem_unupdateoem(tem_code)
                if success:
                    # Xóa thành công nên dùng warning hoặc info để phân biệt màu sắc
                    messages.warning(request, msg_list[0])
                else:
                    messages.error(request, msg_list[0])

    return render(request, 'temoembb.html')


def tembbcusangkd(request):
    # Người dùng gõ thẳng: barcode like '12345%'
    where_clause = request.GET.get('where', '').strip()
    context = {'where': where_clause}

    if where_clause:
        try:
            inserted = run_transfer(where_clause)  # không cần params
            if inserted > 0:
                messages.success(request, f"✅ Đã chèn {inserted} bản ghi.")
            else:
                messages.warning(request, "⚠️ Không có bản ghi nào thỏa điều kiện.")
        except Exception as e:
            messages.error(request, f"❌ Lỗi: {e}")

    return render(request, 'tembbcusangkd.html', context)


def kv1tokv2(request):
    """Xử lý sao chép dữ liệu từ KV1KD sang KV2KD dựa trên barcode."""
    context = {}
    material_id = request.GET.get('barcode')  # Lấy barcode từ query string
    context['barcode'] = material_id or ''   # Gán vào context luôn

    if material_id:
        try:
            # Kết nối đến cả hai cơ sở dữ liệu
            conn_a = get_connection(settings.DATABASES['KV1KD'])
            conn_b = get_connection(settings.DATABASES['KV2KD'])

            result = fetch_related_data(conn_a, material_id)

            if not result:
                messages.error(request, "Mã vạch chưa đúng hoặc không tồn tại trong KV1KD!")
            else:
                mr, cr, fr, ba, wo = result

                # Nếu tất cả đều rỗng
                if all(not x for x in (mr, cr, fr, ba, wo)):
                    messages.error(request, "Không tìm thấy dữ liệu trong KV1KD cho mã vạch này!")
                else:
                    inserted_tables = []

                    if wo:
                        insert_data(conn_b, "kvmes.work_order", wo)
                        inserted_tables.append("work_order")
                    if mr:
                        insert_data(conn_b, "kvmes.material_resource", mr)
                        inserted_tables.append("material_resource")
                    if fr:
                        insert_data(conn_b, "kvmes.feed_record", fr)
                        inserted_tables.append("feed_record")
                    if ba:
                        insert_data(conn_b, "kvmes.batch", ba)
                        inserted_tables.append("batch")
                    if cr:
                        insert_data(conn_b, "kvmes.collect_record", cr)
                        inserted_tables.append("collect_record")

                    if inserted_tables:
                        messages.success(
                            request,
                            f"Đã chèn dữ liệu vào các bảng: {', '.join(inserted_tables)}"
                        )
                    else:
                        messages.warning(request, "Không có bảng nào được chèn dữ liệu!")

        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
        finally:
            if 'conn_a' in locals():
                conn_a.close()
            if 'conn_b' in locals():
                conn_b.close()

    return render(request, 'kv1tokv2.html', context)








def inlaitem(request):
    barcode = request.GET.get("barcode", "").strip()
    results = []

    if barcode:
        if len(barcode) > 7:
            # Tìm kiếm theo cột barcode
            results = Prdebe.objects.filter(barcode=barcode).order_by('-indat', '-intime')
        else:
            # Tìm kiếm theo cột pallet_no
            results = Prdebe.objects.filter(pallet_no=barcode).order_by('-indat', '-intime')

    # Kiểm tra tổng số bản ghi
    total_results = results.count() if results else 0
    if total_results > 20:
        # Áp dụng phân trang nếu số bản ghi > 20
        paginator = Paginator(results, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        results_to_display = page_obj
    else:
        # Hiển thị tất cả bản ghi nếu ≤ 20
        page_obj = None
        results_to_display = results

    return render(request, "inlaitem.html", {
        "query": barcode,
        "results": results_to_display,
        "page_obj": page_obj,
        "total_results": total_results  # Truyền tổng số bản ghi
    })

def clean(value):
    if isinstance(value, str):
        return value.strip()
    return value

def generate_excel(request):
    barcode = request.GET.get("barcode", "").strip()
    printer_name = request.GET.get("printer", "").strip()

    if not barcode or not printer_name:
        return JsonResponse({"success": False, "error": "Thiếu barcode hoặc máy in"})

    # Lấy dữ liệu từ DB
    if len(barcode) > 7:
        data = Prdebe.objects.filter(barcode=barcode).order_by('-indat', '-intime')
    else:
        data = Prdebe.objects.filter(pallet_no=barcode).order_by('-indat', '-intime')

    if not data.exists():
        return JsonResponse({"success": False, "error": "Không tìm thấy dữ liệu"})

    # Lấy bản ghi đầu tiên để truyền vào class
    row = data.first()
    description = ""
    try:
        conn_str = "DRIVER={SQL Server};SERVER=198.1.10.33;DATABASE=BB;UID=kendakv2;PWD=kenda123"
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Barcode FROM dbo.TemOEMBB WHERE Barcode = ?", row.barcode)
            if cursor.fetchone():
                description = "OEM"
    except Exception as e:
        # Nếu lỗi kết nối thì vẫn để description trống, có thể log thêm
        print("Lỗi kết nối BB:", e)

    # Tạo file tạm
    tmp_folder = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(tmp_folder, exist_ok=True)
    tmp_file_path = os.path.join(tmp_folder, f"{barcode}.xlsx")  

    # Gọi class tạo Excel theo template
    excel_path = GetExcelInlaiBB.create_excel(
    partno=clean(row.partno),
    effdat=row.effdat,
    path_file=tmp_file_path,
    slipno=clean(row.slipno),
    barcode=clean(row.barcode),
    ca=clean(row.pclass),
    daylimt=row.daylimt,
    soluong=row.weight,
    mesid=clean(row.mesid),
    machno=clean(row.machno),
    pday=row.prodat,
    indat=row.indat,
    classs=clean(row.pclass),
    intime=row.intime,
    pallet=clean(row.pallet_no),
    loaikeo=clean(row.barcode)[:2] if row.barcode else "",
    description=clean(description),
    masosx=row.some_sx,
)


    if "Lỗi" in excel_path:
        return JsonResponse({"success": False, "error": excel_path})

    try:
        
        #In file ra máy in đã chọn
        win32api.ShellExecute(
            0,
            "printto",
            excel_path,
            f'"{printer_name}"',
            ".",
            0
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    finally:
        os.unlink(excel_path)  # Xóa file tạm

    return JsonResponse({"success": True, "message": "Đã gửi lệnh in thành công"})

def kiemtramokhoabb(request):
    query = request.GET.get('barcode', '').strip()
    result = None

    if query:
        try:
            if len(query) > 10:
                # Tìm trong Prdgdt
                result = Prdgdt.objects.filter(slipno=query).first()
            else:
                # Tìm trong Prdbae
                result = Prdbae.objects.filter(slipno=query).order_by('-id').first()

            # Xử lý thêm nếu có cột reason
            if hasattr(result, 'reason') and result.reason:
                result.reason = result.reason.strip()
            if hasattr(result, 'slipno') and result.reason:
                result.slipno = result.slipno.strip()

        except (Prdbae.DoesNotExist, Prdgdt.DoesNotExist):
            result = None

    context = {
        'query': query,
        'result': result,
    }
    return render(request, 'kiemtramokhoabb.html', context)

@csrf_exempt  # Bỏ qua CSRF cho dễ dàng (chỉ dùng trong phát triển, không khuyến khích cho sản phẩm)
def insert_databaetembb(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Tạo một đối tượng mới và lưu vào cơ sở dữ liệu
        new_record = PrdbaeTemBB(
            subno=data['subno'],
            slipno=data['slipno'],
            stacode=data['stacode'],
            reason=data['reason'],
            indat=data['indat'],
            intime=data['intime'],
            usrno=data['usrno']
        )
        new_record.save()
        
        return JsonResponse({'message': 'Dữ liệu đã được chèn thành công!'}, status=201)
    return JsonResponse({'message': 'Yêu cầu không hợp lệ!'}, status=400)



def kiemtratemquetbb(request):
    query = request.GET.get('barcode', '').strip()
    result = None
    result2 = []
    summary = ""
    summary2 = ""

    servers = ['BB1', 'BB2', 'BB3', 'BB4', 'BB5', 'BB6', 'BB7','BB8']
    # Nếu chưa dùng thì có thể xóa dòng này:
    serversmfnsshare = ['BB1_mfnsshare', 'BB2_mfnsshare', 'BB3_mfnsshare', 'BB4_mfnsshare', 'BB5_mfnsshare', 'BB6_mfnsshare', 'BB7_mfnsshare','BB8_mfnsshare']

    if not query:
        summary = "" #thông báo chưa nhập barcode , nế cần thì thêm zô
    else:
        try:
            if query.startswith('V'):
                result, messages = query_database(servers, AutoSmallScanCode, 'plan_id', query)
            elif query.startswith('R'):
                result, messages = query_database(serversmfnsshare, IFMixPrintLab, 'barcode_lab', query)
            else:
                result, messages = query_database(servers, Mes2RawMaterial, 'barcode', query)

            result2, messages2 = query_database(servers, PptBarCodeRep, 'mater_barcode', query)
            
            summary = ", ".join(messages)
            summary2 = f", {messages2}" if isinstance(messages2, str) else f" {', '.join(messages2)}"
        except (OperationalError, DatabaseError) as e:
            summary = f"Lỗi cơ sở dữ liệu: {str(e)}"
            result = []
        except Exception as e:
            summary = f"Lỗi hệ thống không xác định: {str(e)}"
            result = []

    context = {
        'query': query, 
        'result': result,
        'result2': result2,
        'summary': summary,
        'summary2': summary2,
    }
    return render(request, 'kiemtratemquetbb.html', context)

def query_database(servers, model, filter_field, query_value):
    messages = []
    
    # Trường hợp quét tem -> gom tất cả bản ghi
    if filter_field == 'mater_barcode':
        result = []
        for server in servers:
            try:
                queryset = model.objects.using(server).filter(**{filter_field: query_value})
                if queryset.exists():
                    result.extend(list(queryset))
                    messages.append(f"Máy {server} đã quét {queryset.count()} lần")
                else:
                    messages.append(f"Máy {server} chưa quét")
            except (OperationalError, DatabaseError) as e:
                messages.append(f"Máy {server} tắt (lỗi kết nối: {str(e)})")
        
        if not result:
            messages.append("Không tìm thấy dữ liệu ở máy nào")
        return result, messages

    # Trường hợp khác -> chỉ cần lấy bản ghi đầu tiên
    else:
        result = None
        for server in servers:
            try:
                obj = model.objects.using(server).filter(**{filter_field: query_value}).first()
                if obj:
                    if result is None:  # chỉ lưu object đầu tiên tìm thấy
                        result = obj
                    messages.append(f"Máy {server} có dữ liệu")
                else:
                    messages.append(f"Máy {server} Nodata(quét hết,chưa mở,qúa hạn,lỗi máy chưa có dữ liệu)")
            except (OperationalError, DatabaseError) as e:
                messages.append(f"Máy {server} tắt (lỗi kết nối: {str(e)})")
        
        return result, messages

   

