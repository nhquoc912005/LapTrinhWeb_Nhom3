"""
python manage.py seed_data
Tao du lieu mau cho he thong quan ly van ban.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.core.models import (
    ChiNhanh, DonViNgoai, PhongBan, NguoiDung,
)

User = get_user_model()


# ─────────────────────────────────────────
# DATA DEFINITIONS
# ─────────────────────────────────────────

CHI_NHANH_DATA = [
    "Tong cong ty ATAX",
    "Chi nhanh Ha Noi",
    "Chi nhanh TP Ho Chi Minh",
    "Chi nhanh Da Nang",
]

# Phong ban chung cho moi chi nhanh
PHONG_BAN_CHUNG = [
    "Ban Giam Doc",
    "Phong Ke Toan",
    "Phong Kiem Toan",
    "Phong Tu Van Thue",
    "Phong Hanh Chinh Nhan Su",
    "Phong Dao Tao Chat Luong",
]

DON_VI_NGOAI_DATA = [
    {
        "ten": "Cong ty TNHH Mot Ngay Nang",
        "dia_chi": "123 Nguyen Hue, Q1, TP.HCM",
        "email": "contact@motngaynang.vn",
        "sdt": "0283456789",
    },
    {
        "ten": "Cong ty CP Xay Dung Hoang Gia",
        "dia_chi": "45 Le Duan, Dong Da, Ha Noi",
        "email": "info@hoanggiaxd.vn",
        "sdt": "0243567890",
    },
    {
        "ten": "Cong ty TNHH Thuong Mai Phu Quy",
        "dia_chi": "78 Tran Phu, Hai Chau, Da Nang",
        "email": "office@phuquy.vn",
        "sdt": "0236789012",
    },
    {
        "ten": "Cong ty CP Dau Tu Tan Viet",
        "dia_chi": "99 Hoang Dieu, Binh Thanh, TP.HCM",
        "email": "tanviet@tanviet.vn",
        "sdt": "0287654321",
    },
    {
        "ten": "Cong ty TNHH Dich Vu Kế Toan ABC",
        "dia_chi": "32 Ba Trieu, Hoan Kiem, Ha Noi",
        "email": "ketoanabc@abc.vn",
        "sdt": "0245123456",
    },
    {
        "ten": "Cong ty CP Tai Chinh Mien Trung",
        "dia_chi": "55 Phan Chau Trinh, Son Tra, Da Nang",
        "email": "mientrung@tcmt.vn",
        "sdt": "0234321098",
    },
    {
        "ten": "Ngan hang TMCP Viet Nam Thinh Vuong",
        "dia_chi": "89 Ly Tu Trong, Q1, TP.HCM",
        "email": "vpbank@vpbank.vn",
        "sdt": "0281234567",
    },
    {
        "ten": "Cuc Thue TP Ha Noi",
        "dia_chi": "108 Tran Hung Dao, Hoan Kiem, Ha Noi",
        "email": "cucthuehano@gdt.gov.vn",
        "sdt": "0247654321",
    },
    {
        "ten": "So Ke Hoach Dau Tu TP.HCM",
        "dia_chi": "32 Le Thanh Ton, Q1, TP.HCM",
        "email": "skhdt@tphcm.gov.vn",
        "sdt": "0282345678",
    },
    {
        "ten": "Cong ty CP Kiem Toan GT",
        "dia_chi": "22 Pasteur, Q3, TP.HCM",
        "email": "kiemtoangt@gt.vn",
        "sdt": "0283210987",
    },
    {
        "ten": "Bo Tu Phap - Van Phong Bo",
        "dia_chi": "58-60 Tran Phu, Ba Dinh, Ha Noi",
        "email": "vanphongbo@moj.gov.vn",
        "sdt": "0244567890",
    },
    {
        "ten": "Cong ty TNHH Dau Tu BDS Sunrise",
        "dia_chi": "10 Nguyen Cong Tru, Son Tra, Da Nang",
        "email": "sunrise@sunrise-da.vn",
        "sdt": "0235678901",
    },
    {
        "ten": "Cong ty CP Giao Nhan Van Tai Nhanh",
        "dia_chi": "300 Xa Lo Ha Noi, Q9, TP.HCM",
        "email": "logistic@nhanh.vn",
        "sdt": "0289012345",
    },
    {
        "ten": "Luat su Doan TP.HCM",
        "dia_chi": "45 Dinh Tien Hoang, Binh Thanh, TP.HCM",
        "email": "luatsu@lsdn.vn",
        "sdt": "0283456780",
    },
    {
        "ten": "Cong ty TNHH Phan Mem TechSoft",
        "dia_chi": "77 Cach Mang Thang 8, Q3, TP.HCM",
        "email": "techsoft@techsoft.vn",
        "sdt": "0285678901",
    },
    {
        "ten": "Cong ty CP Bao Hiem Mien Nam",
        "dia_chi": "12 Tran Hung Dao, Q1, TP.HCM",
        "email": "baohiem@bhmn.vn",
        "sdt": "0284321098",
    },
    {
        "ten": "Truong Dai hoc Kinh te Quoc dan",
        "dia_chi": "207 Giai Phong, Hai Ba Trung, Ha Noi",
        "email": "truong@neu.edu.vn",
        "sdt": "0246789012",
    },
    {
        "ten": "Cong ty CP Xuat Nhap Khau Minh Dat",
        "dia_chi": "88 Lo Duc, Hai Ba Trung, Ha Noi",
        "email": "export@minhdat.vn",
        "sdt": "0248901234",
    },
    {
        "ten": "Cong ty TNHH San Xuat Co Khi Tien Dat",
        "dia_chi": "KCN Bien Hoa 2, Dong Nai",
        "email": "cokhi@tiendat.vn",
        "sdt": "0251234567",
    },
    {
        "ten": "Hoa Xa Hoi - Ubnd Quan 1",
        "dia_chi": "86 Le Thanh Ton, Q1, TP.HCM",
        "email": "ubnd@quan1.hochiminhcity.gov.vn",
        "sdt": "0282109876",
    },
]

# Nguoi dung theo chuc vu va phong ban
# Format: (ho_va_ten, email, sdt, chuc_vu, username, password)
NGUOI_DUNG_TCT = [
    # Ban Giam Doc - Lanh dao
    ("Nguyen Van Hung", "hung.gd@atax.vn", "0901234567", "Lanh Dao", "hung.gd", "123456"),
    ("Le Thi Lan", "lan.pgd@atax.vn", "0912345678", "Lanh Dao", "lan.pgd", "123456"),
    # Phong Ke Toan
    ("Tran Thi Mai", "mai.kt@atax.vn", "0923456789", "Chuyen Vien", "mai.kt", "123456"),
    ("Pham Van Duc", "duc.kt@atax.vn", "0934567890", "Chuyen Vien", "duc.kt", "123456"),
    ("Nguyen Thi Hoa", "hoa.kt@atax.vn", "0945678901", "Chuyen Vien", "hoa.kt", "123456"),
    # Phong Kiem Toan
    ("Do Van Minh", "minh.kta@atax.vn", "0956789012", "Lanh Dao", "minh.kta", "123456"),
    ("Ngo Thi Thu", "thu.kta@atax.vn", "0967890123", "Chuyen Vien", "thu.kta", "123456"),
    ("Bui Van Nam", "nam.kta@atax.vn", "0978901234", "Chuyen Vien", "nam.kta", "123456"),
    # Phong Tu Van Thue
    ("Vo Thi Bich", "bich.tvt@atax.vn", "0989012345", "Chuyen Vien", "bich.tvt", "123456"),
    ("Ho Van Long", "long.tvt@atax.vn", "0990123456", "Chuyen Vien", "long.tvt", "123456"),
    # Phong HC NS
    ("Nguyen Van Tu", "tu.hcns@atax.vn", "0901357924", "Lanh Dao", "tu.hcns", "123456"),
    ("Tran Thi Kim", "kim.hcns@atax.vn", "0912468135", "Chuyen Vien", "kim.hcns", "123456"),
    # Phong Dao Tao Chat Luong
    ("Le Van Thanh", "thanh.dt@atax.vn", "0923579246", "Chuyen Vien", "thanh.dt", "123456"),
    ("Dinh Thi Nga", "nga.dt@atax.vn", "0934680357", "Chuyen Vien", "nga.dt", "123456"),
    # Van thu
    ("Truong Thi Khanh", "khanh.vt@atax.vn", "0945791468", "Van Thu", "khanh.vt", "123456"),
    ("Pham Van Hai", "hai.vt@atax.vn", "0956802579", "Van Thu", "hai.vt", "123456"),
]

NGUOI_DUNG_HN = [
    ("Tran Van Khoa", "khoa.hn@atax.vn", "0243112233", "Lanh Dao", "khoa.hn", "123456"),
    ("Nguyen Thi Linh", "linh.hn@atax.vn", "0243223344", "Chuyen Vien", "linh.hn", "123456"),
    ("Do Thi Thanh", "thanh.hn@atax.vn", "0243334455", "Chuyen Vien", "thanh.hn", "123456"),
    ("Le Van Nam", "nam.hn@atax.vn", "0243445566", "Lanh Dao", "nam.hn", "123456"),
    ("Pham Thi Hue", "hue.hn@atax.vn", "0243556677", "Chuyen Vien", "hue.hn", "123456"),
    ("Bui Van An", "an.hn@atax.vn", "0243667788", "Chuyen Vien", "an.hn", "123456"),
    ("Vo Thi Xuan", "xuan.hn@atax.vn", "0243778899", "Chuyen Vien", "xuan.hn", "123456"),
    ("Ho Van Phuc", "phuc.hn@atax.vn", "0243889900", "Lanh Dao", "phuc.hn", "123456"),
    ("Nguyen Van Tuan", "tuan.hn@atax.vn", "0243990011", "Chuyen Vien", "tuan.hn", "123456"),
    ("Tran Thi Dung", "dung.hn@atax.vn", "0244011223", "Van Thu", "dung.hn", "123456"),
    ("Le Thi Hong", "hong.hn@atax.vn", "0244122334", "Chuyen Vien", "hong.hn", "123456"),
    ("Pham Van Thi", "thi.hn@atax.vn", "0244233445", "Chuyen Vien", "thi.hn", "123456"),
]

NGUOI_DUNG_HCM = [
    ("Nguyen Thi Phuong", "phuong.hcm@atax.vn", "0281234560", "Lanh Dao", "phuong.hcm", "123456"),
    ("Le Van Cuong", "cuong.hcm@atax.vn", "0282345671", "Chuyen Vien", "cuong.hcm", "123456"),
    ("Tran Thi Loan", "loan.hcm@atax.vn", "0283456782", "Chuyen Vien", "loan.hcm", "123456"),
    ("Do Van Hung", "hung.hcm@atax.vn", "0284567893", "Lanh Dao", "hung.hcm", "123456"),
    ("Ngo Thi Yen", "yen.hcm@atax.vn", "0285678904", "Chuyen Vien", "yen.hcm", "123456"),
    ("Bui Thi My", "my.hcm@atax.vn", "0286789015", "Chuyen Vien", "my.hcm", "123456"),
    ("Vo Van Hai", "hai.hcm@atax.vn", "0287890126", "Chuyen Vien", "hai.hcm", "123456"),
    ("Pham Thi Thu", "thu.hcm@atax.vn", "0288901237", "Lanh Dao", "thu.hcm", "123456"),
    ("Ho Van Lam", "lam.hcm@atax.vn", "0289012348", "Chuyen Vien", "lam.hcm", "123456"),
    ("Nguyen Van Kiet", "kiet.hcm@atax.vn", "0281123459", "Van Thu", "kiet.hcm", "123456"),
    ("Tran Van Son", "son.hcm@atax.vn", "0282234560", "Chuyen Vien", "son.hcm", "123456"),
    ("Le Thi Ngoc", "ngoc.hcm@atax.vn", "0283345671", "Chuyen Vien", "ngoc.hcm", "123456"),
]

NGUOI_DUNG_DN = [
    ("Nguyen Van Bao", "bao.dn@atax.vn", "0236112233", "Lanh Dao", "bao.dn", "123456"),
    ("Tran Thi Nhu", "nhu.dn@atax.vn", "0236223344", "Chuyen Vien", "nhu.dn", "123456"),
    ("Le Van Hieu", "hieu.dn@atax.vn", "0236334455", "Chuyen Vien", "hieu.dn", "123456"),
    ("Do Thi Cam", "cam.dn@atax.vn", "0236445566", "Lanh Dao", "cam.dn", "123456"),
    ("Pham Van Loc", "loc.dn@atax.vn", "0236556677", "Chuyen Vien", "loc.dn", "123456"),
    ("Bui Thi Tuyet", "tuyet.dn@atax.vn", "0236667788", "Chuyen Vien", "tuyet.dn", "123456"),
    ("Vo Van Tri", "tri.dn@atax.vn", "0236778899", "Chuyen Vien", "tri.dn", "123456"),
    ("Ho Thi Nhung", "nhung.dn@atax.vn", "0236889900", "Lanh Dao", "nhung.dn", "123456"),
    ("Ngo Van Dai", "dai.dn@atax.vn", "0236990011", "Chuyen Vien", "dai.dn", "123456"),
    ("Nguyen Thi Hien", "hien.dn@atax.vn", "0237011223", "Van Thu", "hien.dn", "123456"),
    ("Tran Van Binh", "binh.dn@atax.vn", "0237122334", "Chuyen Vien", "binh.dn", "123456"),
    ("Le Thi Truc", "truc.dn@atax.vn", "0237233445", "Chuyen Vien", "truc.dn", "123456"),
]

CHUC_VU_MAP = {
    "Lanh Dao":   NguoiDung.ChucVu.LANH_DAO,
    "Chuyen Vien": NguoiDung.ChucVu.CHUYEN_VIEN,
    "Van Thu":     NguoiDung.ChucVu.VAN_THU,
    "Quan Tri":    NguoiDung.ChucVu.QUAN_TRI,
}

# Chi nhanh -> phong ban index -> nguoi dung list
CHI_NHANH_ND_MAP = {
    0: NGUOI_DUNG_TCT,   # Tong cong ty
    1: NGUOI_DUNG_HN,    # Ha Noi
    2: NGUOI_DUNG_HCM,   # TP.HCM
    3: NGUOI_DUNG_DN,    # Da Nang
}

# Phan bo nguoi dung vao phong ban (index trong list phong ban)
# moi chi nhanh co 6 phong ban, phan bo nhu sau:
PHAN_BO_TCT = [
    0,  # Ban Giam Doc -> 2 ng (idx 0,1)
    0,
    2,  # Phong Ke Toan -> 3 ng (idx 2,3,4)
    2,
    2,
    3,  # Phong Kiem Toan -> 3 ng (idx 5,6,7)
    3,
    3,
    4,  # Phong Tu Van Thue -> 2 ng (idx 8,9)
    4,
    5,  # Phong HCNS -> 2 ng (idx 10,11)
    5,
    6,  # Phong Dao Tao -> 2 ng (idx 12,13)
    6,
    7,  # Van thu -> (idx 14,15) - no phong ban specific
    7,
]

PHAN_BO_CN = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]


class Command(BaseCommand):
    help = "Seed du lieu mau cho he thong"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Xoa du lieu cu truoc khi seed",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Dang xoa du lieu cu..."))
            NguoiDung.objects.all().delete()
            PhongBan.objects.all().delete()
            DonViNgoai.objects.all().delete()
            ChiNhanh.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Da xoa xong."))

        # ── 1. Chi nhanh ──
        self.stdout.write("Tao chi nhanh...")
        chi_nhanh_objs = []
        for ten in CHI_NHANH_DATA:
            cn, created = ChiNhanh.objects.get_or_create(ten_chi_nhanh=ten)
            chi_nhanh_objs.append(cn)
            if created:
                self.stdout.write(f"  + ChiNhanh: {ten}")

        # ── 2. Don vi ngoai ──
        self.stdout.write("Tao don vi ngoai...")
        for dv in DON_VI_NGOAI_DATA:
            obj, created = DonViNgoai.objects.get_or_create(
                email=dv["email"],
                defaults={
                    "ten_don_vi":   dv["ten"],
                    "dia_chi":      dv["dia_chi"],
                    "so_dien_thoai": dv["sdt"],
                },
            )
            if created:
                self.stdout.write(f"  + DonViNgoai: {dv['ten']}")

        # ── 3. Phong ban + NguoiDung theo chi nhanh ──
        for idx, cn in enumerate(chi_nhanh_objs):
            self.stdout.write(f"Tao phong ban cho: {cn.ten_chi_nhanh}")
            pb_list = []
            for pb_ten in PHONG_BAN_CHUNG:
                pb, created = PhongBan.objects.get_or_create(
                    chi_nhanh=cn,
                    ten_phong_ban=pb_ten,
                )
                pb_list.append(pb)
                if created:
                    self.stdout.write(f"  + PhongBan: {pb_ten} ({cn.ten_chi_nhanh})")

            # Nguoi dung
            nd_list = CHI_NHANH_ND_MAP.get(idx, [])
            if idx == 0:
                phan_bo = PHAN_BO_TCT
            else:
                phan_bo = PHAN_BO_CN

            for i, nd_data in enumerate(nd_list):
                ho_va_ten, email, sdt, cv_str, username, password = nd_data
                chuc_vu = CHUC_VU_MAP.get(cv_str, NguoiDung.ChucVu.CHUYEN_VIEN)

                # Tai khoan
                user, u_created = User.objects.get_or_create(
                    username=username,
                    defaults={"email": email},
                )
                if u_created:
                    user.set_password(password)
                    user.save()

                # Phong ban
                if idx == 0:
                    pb_idx = phan_bo[i] if i < len(phan_bo) else 0
                    phong_ban = pb_list[pb_idx] if pb_idx < len(pb_list) else pb_list[0]
                else:
                    pb_idx = phan_bo[i % len(phan_bo)] if phan_bo else 0
                    phong_ban = pb_list[pb_idx] if pb_idx < len(pb_list) else pb_list[0]

                if chuc_vu == NguoiDung.ChucVu.VAN_THU:
                    phong_ban = None  # Van thu khong gan phong ban cu the

                nd, nd_created = NguoiDung.objects.get_or_create(
                    email=email,
                    defaults={
                        "tai_khoan": user,
                        "phong_ban": phong_ban,
                        "ho_va_ten": ho_va_ten,
                        "chuc_vu":   chuc_vu,
                        "sdt":       sdt,
                    },
                )
                if nd_created:
                    self.stdout.write(f"  + NguoiDung: {ho_va_ten} ({cv_str}) - {cn.ten_chi_nhanh}")

        # ── 4. Ket qua ──
        self.stdout.write(self.style.SUCCESS("\n=== SEED HOAN THANH ==="))
        self.stdout.write(f"  ChiNhanh:   {ChiNhanh.objects.count()}")
        self.stdout.write(f"  PhongBan:   {PhongBan.objects.count()}")
        self.stdout.write(f"  DonViNgoai: {DonViNgoai.objects.count()}")
        self.stdout.write(f"  NguoiDung:  {NguoiDung.objects.count()}")
        self.stdout.write(f"  User:       {User.objects.count()}")
