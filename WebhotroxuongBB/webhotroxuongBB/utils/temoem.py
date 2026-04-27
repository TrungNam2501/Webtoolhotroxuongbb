from django.utils import timezone
from django.db import OperationalError, DatabaseError
# Import tuyệt đối từ models của app để tránh lỗi "parent package"
from ..models import TemOEMBB, RtPlan2CWSS, Prdebe

class TemOEMHandler:
    def __init__(self, servers=None):
        # Nếu truyền servers thì dùng, không thì mặc định là máy đích 33BB
        self.servers = servers or ['33BB']

    # ================= BB =================

    def bb_insert_one(self, tem_code):
        source_db = 'default'  # Nguồn lấy dữ liệu (Prdebe)
        target_db = '33BB'     # Đích chèn dữ liệu (TemOEMBB)
        
        try:
            # 1. KIỂM TRA ĐÍCH: Có rồi thì thôi
            exists_at_target = TemOEMBB.objects.using(target_db).filter(barcode=tem_code).exists()
            if exists_at_target:
                return False, [f"Bảng TemOEMBB 10.33 db:BB. Tem {tem_code} đã có rồi."]

            # 2. CHƯA CÓ: Sang nguồn 'default' tìm thông tin
            ebe_info = Prdebe.objects.using(source_db).filter(barcode=tem_code).first()
            
            if not ebe_info:
                return False, [f"Lỗi: Không thấy tem {tem_code} ở table prdebe 10.33 db:erp (Nhập tem sai rồi)"]

            # 3. THỰC HIỆN INSERT
            now = timezone.now()
            TemOEMBB.objects.using(target_db).create(
                barcode=ebe_info.barcode,
                mesid=ebe_info.mesid,
                partno=ebe_info.partno,
                indat=now.strftime('%Y%m%d'),  # Định dạng yyyymmdd
                intime=now.strftime('%H:%M:%S') # Định dạng hh:mm:ss
            )
            
            return True, [f"Bảng TemOEMBB 10.33 db:BB. Thêm thành công tem {tem_code}"]

        except Exception as e:
            return False, [f"Lỗi hệ thống: {str(e)}"]

    
    def bb_insert_all(self, tem_code):
        source_db = 'default'
        target_db = '33BB'
        results_messages = []
        
        try:
            # BƯỚC 1: Tìm mesid từ mã vạch truyền vào
            root_item = Prdebe.objects.using(source_db).filter(barcode=tem_code).first()
            
            if not root_item:
                return False, [f"Lỗi: Không thấy tem {tem_code} ở table prdebe 10.33 db:erp (Nhập tem sai rồi)"]
            
            target_mesid = root_item.mesid
            
            # BƯỚC 2: Truy vấn tất cả các tem có cùng mesid này
            all_group_items = Prdebe.objects.using(source_db).filter(mesid=target_mesid)
            
            total_in_group = all_group_items.count()
            count_inserted = 0
            count_skipped = 0

            now = timezone.now()
            current_date = now.strftime('%Y%m%d')
            current_time = now.strftime('%H:%M:%S')

            # BƯỚC 3: Lặp và Insert vào đích (bỏ qua nếu đã tồn tại)
            for item in all_group_items:
                exists = TemOEMBB.objects.using(target_db).filter(barcode=item.barcode).exists()
                
                if not exists:
                    TemOEMBB.objects.using(target_db).create(
                        barcode=item.barcode,
                        mesid=item.mesid,
                        partno=item.partno,
                        indat=current_date,
                        intime=current_time
                    )
                    count_inserted += 1
                else:
                    count_skipped += 1
            
            # Trả về thông báo chi tiết
            msg = (f"MESID: {target_mesid} | Tổng nhóm: {total_in_group} tem. "
                   f"Đã thêm mới: {count_inserted}, Đã bỏ qua (trùng): {count_skipped}")
            
            return True, [msg]

        except Exception as e:
            return False, [f"Lỗi hệ thống: {str(e)}"]

    def bb_delete(self, tem_code):
        source_db = 'default'
        target_db = '33BB'
        
        try:
            # 1. Tìm mesid
            root_item = Prdebe.objects.using(source_db).filter(barcode=tem_code).first()
            if not root_item:
                return False, [f"Lỗi: Không thấy tem {tem_code} ở table prdebe 10.33 db:erp (Nhập tem sai rồi)"]

            target_mesid = root_item.mesid
            
            # 2. Lấy danh sách barcode và ÉP KIỂU THÀNH LIST (Quan trọng nhất ở đây)
            # Thêm list(...) để đưa dữ liệu về RAM, tránh lỗi Subquery giữa 2 DB
            barcodes_in_group = list(
                Prdebe.objects.using(source_db)
                .filter(mesid=target_mesid)
                .values_list('barcode', flat=True)
            )
            
            if not barcodes_in_group:
                return True, [f"MESID {target_mesid}: Nhóm này không có mã vạch nào."]

            # 3. Thực hiện xóa tại server đích (Lúc này barcodes_in_group đã là 1 list Python thuần túy)
            deleted_count, _ = TemOEMBB.objects.using(target_db).filter(barcode__in=barcodes_in_group).delete()
            
            if deleted_count > 0:
                return True, [f"MESID {target_mesid}: Đã xóa thành công {deleted_count} tem tại TemOEMBB 10.33 db:BB."]
            else:
                return True, [f"MESID {target_mesid}: Không tìm thấy tem nào để xóa tại TemOEMBB 10.33 db:BB."]

        except Exception as e:
            return False, [f"Lỗi hệ thống: {str(e)}"]
    
    # ================= HÓA CHẤT (RtPlan2CWSS) =================

    def chem_updateoem(self, tem_code):
        target_db = '33BB'
        
        try:
            # 1. Lấy QuerySet các bản ghi khớp plan_id tại máy đích
            target_queryset = RtPlan2CWSS.objects.using(target_db).filter(plan_id=tem_code)

            # 2. Kiểm tra tồn tại: Nếu không tìm thấy mã nào thì báo lỗi
            if not target_queryset.exists():
                return False, [f"Mã Plan ID {tem_code} không tồn tại trên bảng 'IF_RtPlan2CWSS' (DB: 10.33)."]

            # 3. Kiểm tra trạng thái OEM: 
            # Tìm xem trong những bản ghi đó, có cái nào CHƯA phải là 'OEM' không
            needs_update = target_queryset.exclude(oem="OEM")

            if not needs_update.exists():
                return False, [f"Mã Plan ID {tem_code} đã được cập nhật 'OEM' từ trước rồi."]

            # 4. THỰC HIỆN UPDATE: Chỉ cập nhật những bản ghi chưa có chữ OEM
            updated_count = needs_update.update(oem="OEM")
            
            return True, [f"Đã cập nhật thành công 'OEM' cho {updated_count} dòng của Plan ID {tem_code}."]

        except Exception as e:
            return False, [f"Lỗi hệ thống update hóa chất: {str(e)}"]

    def chem_unupdateoem(self, tem_code):
        target_db = '33BB'
        
        try:
            # 1. Lấy QuerySet các bản ghi khớp plan_id tại máy đích
            target_queryset = RtPlan2CWSS.objects.using(target_db).filter(plan_id=tem_code)

            # 2. Kiểm tra tồn tại: Nếu không tìm thấy mã nào trong bảng thì báo lỗi
            if not target_queryset.exists():
                return False, [f"Mã Plan ID {tem_code} không tồn tại trên bảng 'IF_RtPlan2CWSS' (DB: 10.33)."]

            # 3. Kiểm tra trạng thái: 
            # Tìm xem có bản ghi nào ĐANG LÀ 'OEM' (hoặc khác 'KD') để cần đưa về 'KD' không
            needs_revert = target_queryset.exclude(oem="KD")

            if not needs_revert.exists():
                return False, [f"Mã Plan ID {tem_code} hiện đã ở trạng thái thường (KD) rồi, không cần hoàn tác."]

            # 4. THỰC HIỆN UPDATE trực tiếp về 'KD'
            updated_count = needs_revert.update(oem="KD")
            
            return True, [f"Đã cập nhật thành công về trạng thái thường (KD) cho {updated_count} dòng của Plan ID {tem_code}."]

        except Exception as e:
            return False, [f"Lỗi hệ thống hoàn tác hóa chất: {str(e)}"]