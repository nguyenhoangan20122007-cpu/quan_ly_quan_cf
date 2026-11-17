from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import lay_csdl
from app.dependencies import yeu_cau_nhan_vien
from app.models import ChiTietDonHang, DanhMuc, DonHang, KhachHang, NguoiDung, SanPham
from app.schemas import DuLieuDonHang


router = APIRouter()


# Tao don hang: Admin va nhan vien
@router.post("/orders", status_code=201)
def tao_don_hang(
    du_lieu: DuLieuDonHang,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    if (
        du_lieu.ma_khach_hang is not None
        and not csdl.get(KhachHang, du_lieu.ma_khach_hang)
    ):
        raise HTTPException(404, "Không tìm thấy khách hàng")

    danh_sach_san_pham = {}

    for dong in du_lieu.chi_tiet:
        if dong.ma_san_pham in danh_sach_san_pham:
            continue

        # Giữ khóa đọc đến khi ghi đơn để trạng thái không đổi sau khi kiểm tra.
        ket_qua = csdl.execute(
            select(SanPham, DanhMuc.trang_thai)
            .outerjoin(SanPham.danh_muc)
            .where(SanPham.ma == dong.ma_san_pham)
            .with_for_update(read=True)
        ).one_or_none()
        if ket_qua is None:
            raise HTTPException(
                404,
                "Không tìm thấy đồ uống"
            )

        san_pham, trang_thai_danh_muc = ket_qua
        if san_pham.trang_thai != "available":
            raise HTTPException(
                status_code=409,
                detail=f"Đồ uống {san_pham.ten} đã ngừng bán"
            )
        if trang_thai_danh_muc != "active":
            raise HTTPException(
                status_code=409,
                detail=f"Danh mục của sản phẩm {san_pham.ten} đang tạm ẩn"
            )

        danh_sach_san_pham[dong.ma_san_pham] = san_pham

    don_hang = DonHang(
        ma_nhan_vien=nguoi_dung.ma,
        ma_khach_hang=du_lieu.ma_khach_hang,
        trang_thai="pending",
        tong_tien=Decimal("0"),
        phuong_thuc_thanh_toan=None,
        trang_thai_thanh_toan="unpaid",
        ngay_thanh_toan=None
    )

    tong_tien = Decimal("0")

    for dong in du_lieu.chi_tiet:
        san_pham = danh_sach_san_pham[dong.ma_san_pham]

        don_hang.chi_tiet.append(
            ChiTietDonHang(
                ma_san_pham=san_pham.ma,
                so_luong=dong.so_luong,
                don_gia=san_pham.gia,
                phan_tram_duong=dong.phan_tram_duong,
                muc_da=dong.muc_da,
                ghi_chu=dong.ghi_chu
            )
        )

        tong_tien += san_pham.gia * dong.so_luong

    don_hang.tong_tien = tong_tien

    csdl.add(don_hang)
    csdl.commit()
    csdl.refresh(don_hang)

    return {
        "ma": don_hang.ma,
        "trang_thai": don_hang.trang_thai,
        "tong_tien": float(don_hang.tong_tien)
    }
