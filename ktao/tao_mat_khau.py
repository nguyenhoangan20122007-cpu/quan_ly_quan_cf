from app.security import bam_mat_khau
from app.database import PhienLamViec
from app.models import NguoiDung

csdl = PhienLamViec()

try:
    danh_sach_tai_khoan = [
        ("admin", "Admin@123456", "admin"),
        ("nhanvien1", "Nhanvien@123456", "staff"),
        ("nhanvien2", "Nhanvien@123456", "staff")
    ]

    for ten_dang_nhap, mat_khau, vai_tro in danh_sach_tai_khoan:
        nguoi_dung = csdl.query(NguoiDung).filter(
            NguoiDung.ten_dang_nhap == ten_dang_nhap
        ).first()

        if nguoi_dung is None:
            nguoi_dung = NguoiDung(
                ten_dang_nhap=ten_dang_nhap,
                mat_khau_bam=bam_mat_khau(mat_khau),
                vai_tro=vai_tro
            )
            csdl.add(nguoi_dung)
        else:
            nguoi_dung.mat_khau_bam = bam_mat_khau(mat_khau)
            nguoi_dung.vai_tro = vai_tro

    csdl.commit()
    print("Da tao va cap nhat tai khoan thanh cong!")

except Exception as loi:
    csdl.rollback()
    print("Loi:", loi)

finally:
    csdl.close()