from django.db import models

class Prdebe(models.Model):
    subno = models.CharField(max_length=1)
    factory = models.CharField(max_length=1)
    mesid = models.CharField(max_length=20, null=True, blank=True)
    machno = models.CharField(max_length=20)
    daylimt = models.IntegerField()
    barcode = models.CharField(max_length=20, primary_key=True)
    slipno = models.CharField(max_length=20)
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    prodat = models.CharField(max_length=8)
    effdat = models.CharField(max_length=8)
    pclass = models.CharField(max_length=1, db_column='class')
    ptype = models.CharField(max_length=1)
    status = models.CharField(max_length=1, null=True, blank=True)
    partno = models.CharField(max_length=20)
    intime = models.CharField(max_length=8)
    indat = models.CharField(max_length=8)
    usrno = models.CharField(max_length=8)
    pallet_no = models.CharField(max_length=6, null=True, blank=True)
    active = models.CharField(max_length=1, null=True, blank=True)
    some_sx = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'prdebe'
        managed = False


class Prdbae(models.Model):
    subno = models.CharField(max_length=1)
    slipno = models.CharField(max_length=16)
    stacode = models.CharField(max_length=1)
    reason = models.CharField(max_length=40)
    indat = models.CharField(max_length=8)
    intime = models.CharField(max_length=8)
    usrno = models.CharField(max_length=8)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'prdbae'

class Prdgdt(models.Model):
    subno = models.CharField(max_length=1)
    slipno = models.CharField(max_length=16)
    stacode = models.CharField(max_length=1)
    reason = models.CharField(max_length=40)
    indat = models.CharField(max_length=8)
    intime = models.CharField(max_length=8)
    usrno = models.CharField(max_length=8)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'prdgdt'

class PrdbaeTemBB(models.Model):
    subno = models.CharField(max_length=1)
    slipno = models.CharField(max_length=16)
    stacode = models.CharField(max_length=1)
    reason = models.CharField(max_length=40)
    indat = models.CharField(max_length=8)
    intime = models.CharField(max_length=8)
    usrno = models.CharField(max_length=8)
    class Meta:
        db_table = 'prdbae_temBB'
        managed = False

class Mes2RawMaterial(models.Model):
    equip_code = models.CharField(max_length=20, null=True, db_column='EquipCode')
    barcode = models.CharField(max_length=50, primary_key=True, db_column='Barcode')  # <--- thêm primary_key=True
    material_code = models.CharField(max_length=50, null=True, db_column='MaterialCode')
    package_count = models.CharField(max_length=10, null=True, db_column='PackageCount')
    per_package_weight = models.IntegerField(null=True, db_column='PerPackageWeight')
    lot_number = models.CharField(max_length=50, null=True, db_column='LotNumber')
    product_date = models.CharField(max_length=50, null=True, db_column='ProductDate')
    valid_date = models.CharField(max_length=50, null=True, db_column='ValidDate')
    product_name = models.CharField(max_length=50, null=True, db_column='ProductName')
    record_time = models.DateTimeField(null=True, db_column='RecordTime')
    up_flag = models.CharField(max_length=1, null=True, db_column='UpFlag')
    remark = models.CharField(max_length=20, null=True, db_column='Remark')

    class Meta:
        db_table = 'Mes2RawMaterial'
        managed = False


class AutoSmallScanCode(models.Model):
    plan_id = models.CharField(db_column='Plan_Id', max_length=20, primary_key=True)
    prd_date = models.CharField(db_column='Prd_Date', max_length=8)
    end_date = models.CharField(db_column='End_Date', max_length=8)
    recipe_id = models.CharField(db_column='Recipe_ID', max_length=30)
    equip_code = models.CharField(db_column='Equip_Code', max_length=30, null=True, blank=True)
    plan_date = models.CharField(db_column='Plan_Date', max_length=30, null=True, blank=True)
    weight = models.DecimalField(db_column='Weight', max_digits=8, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(db_column='Active', null=True, blank=True)

    class Meta:
        managed = False   # vì bạn không muốn Django tự sửa bảng
        db_table = 'AutoSmall_ScanCode'

class IFMixPrintLab(models.Model):
    id = models.AutoField(primary_key=True, db_column='ID')
    mix_save_time = models.CharField(max_length=20, null=True, db_column='MixSaveTime')
    shift = models.CharField(max_length=8, null=True, db_column='Shift')
    barcode = models.CharField(max_length=20, null=True, db_column='Barcode')
    equip_id = models.IntegerField(null=True, db_column='Equip_ID')
    plan_id = models.CharField(max_length=20, null=True, db_column='Plan_ID')
    recipe_code = models.CharField(max_length=50, null=True, db_column='Recipe_Code')
    recipe_name = models.CharField(max_length=50, null=True, db_column='Recipe_Name')
    recipe_type = models.IntegerField(null=True, db_column='Recipe_Type')
    set_num = models.IntegerField(null=True, db_column='Set_Num')
    serial_num = models.IntegerField(null=True, db_column='Serial_Num')
    shift_num = models.IntegerField(null=True, db_column='ShiftNum')
    daily_limit = models.IntegerField(null=True, db_column='Dailylimit')
    weight = models.DecimalField(max_digits=8, decimal_places=3, db_column='Weight')
    barcode_lab = models.CharField(max_length=50, null=True, db_column='BarCodeLab')
    write_time = models.CharField(max_length=20, null=True, db_column='Write_Time')
    read_time = models.CharField(max_length=20, null=True, db_column='Read_Time')
    rw_flag = models.CharField(max_length=1, null=True, db_column='RW_Flag')
    active = models.BooleanField(null=True, db_column='Active')

    class Meta:
        db_table = 'IF_MixPrintLab'
        managed = False

class PptBarCodeRep(models.Model):
    pkid = models.CharField(primary_key=True, max_length=40)
    barcode = models.CharField(max_length=20, db_column='Barcode')
    mater_barcode = models.CharField(max_length=16, db_column='Mater_Barcode')
    save_time = models.CharField(max_length=50, null=True, db_column='SaveTime')
    equip_id = models.IntegerField(null=True, db_column='Equip_ID')
    plan_id = models.CharField(max_length=20, null=True, db_column='Plan_ID')
    recipe_code = models.CharField(max_length=50, null=True, db_column='Recipe_Code')
    recipe_name = models.CharField(max_length=50, null=True, db_column='Recipe_Name')
    set_num = models.IntegerField(null=True, db_column='Set_Num')
    serial_num = models.IntegerField(null=True, db_column='Serial_Num')
    mater_code = models.CharField(max_length=50, null=True, db_column='Mater_Code')
    mater_name = models.CharField(max_length=50, null=True, db_column='Mater_Name')
    mater_type = models.IntegerField(null=True, db_column='Mater_Type')
    flg = models.CharField(max_length=1, null=True, db_column='Flg', default='N')

    class Meta:
        db_table = 'Vw_Ppt_BarCodeRep'
        managed = False



class TemOEMBB(models.Model):
    mesid = models.CharField(max_length=20, null=True, blank=True)
    partno = models.CharField(max_length=20, null=True, blank=True)
    # Primary Key dựa trên Barcode như trong SQL script
    barcode = models.CharField(max_length=20, primary_key=True, db_column='Barcode')
    indat = models.CharField(max_length=10, null=True, blank=True)
    intime = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'TemOEMBB'  # Đảm bảo trùng tên bảng trong SQL Server
        managed = False         # Để Django có thể tạo/sửa bảng nếu cần

    def __str__(self):
        return self.barcode
    
class RtPlan2CWSS(models.Model):
    plan_id = models.CharField(max_length=20, primary_key=True, db_column='Plan_Id')
    equip_code = models.CharField(max_length=50, null=True, blank=True, db_column='Equip_Code')
    plan_serial = models.IntegerField(null=True, blank=True, db_column='Plan_Serial')
    recipe_id = models.CharField(max_length=50, null=True, blank=True, db_column='Recipe_ID')
    recipe_code = models.CharField(max_length=50, null=True, blank=True, db_column='Recipe_Code')
    recipe_name = models.CharField(max_length=50, null=True, blank=True, db_column='Recipe_Name')
    version = models.CharField(max_length=50, null=True, blank=True, db_column='Version')
    mixer_line = models.CharField(max_length=50, null=True, blank=True, db_column='Mixer_Line')
    shift_id = models.CharField(max_length=10, null=True, blank=True, db_column='Shift_Id')
    plan_num = models.IntegerField(null=True, blank=True, db_column='Plan_Num')
    start_date = models.CharField(max_length=20, null=True, blank=True, db_column='Start_Date')
    end_date = models.CharField(max_length=50, null=True, blank=True, db_column='End_Date')
    plan_batch = models.CharField(max_length=50, null=True, blank=True, db_column='Plan_Batch')
    plan_state = models.IntegerField(null=True, blank=True, db_column='Plan_State')
    plan_date = models.CharField(max_length=50, null=True, blank=True, db_column='Plan_Date')
    write_time = models.CharField(max_length=20, null=True, blank=True, db_column='Write_Time')
    read_time = models.CharField(max_length=20, null=True, blank=True, db_column='Read_Time')
    rw_flag = models.IntegerField(null=True, blank=True, db_column='RW_Flag')
    oem = models.CharField(max_length=10, null=True, blank=True, db_column='OEM')

    class Meta:
        db_table = 'IF_RtPlan2CWSS'  # Tên bảng chính xác trong SQL Server
        managed = False              # Không sửa bảng

    def __str__(self):
        return self.plan_id