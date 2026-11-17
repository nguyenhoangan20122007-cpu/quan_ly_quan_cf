from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import lay_csdl
from app.dependencies import yeu_cau_nhan_vien
from app.models import ChiTietDonHang, DonHang, NguoiDung, SanPham
from app.schemas import DuLieuThanhToan


router = APIRouter()


def thong_tin_don_hang(don: DonHang):
    return {
        "ma": don.ma,
        "trang_thai": don.trang_thai,
        "tong_tien": float(don.tong_tien),
        "ngay_tao": don.ngay_tao.isoformat(),
        "phuong_thuc_thanh_toan": don.phuong_thuc_thanh_toan,
        "trang_thai_thanh_toan": don.trang_thai_thanh_toan,
        "ngay_thanh_toan": don.ngay_thanh_toan.isoformat() if don.ngay_thanh_toan else None
    }


# Xem don hang: Admin va nhan vien
@router.get("/orders")
def xem_don_hang(
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    danh_sach = csdl.scalars(select(DonHang).order_by(DonHang.ma.desc()))
    return [thong_tin_don_hang(don) for don in danh_sach]


@router.get("/orders/{ma}")
def chi_tiet_don_hang(
    ma: int,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    don_hang = csdl.get(DonHang, ma)
    if don_hang is None:
        raise HTTPException(404, "Không tìm thấy đơn hàng")

    chi_tiet = csdl.execute(
        select(ChiTietDonHang, SanPham.ten)
        .outerjoin(SanPham, ChiTietDonHang.ma_san_pham == SanPham.ma)
        .where(ChiTietDonHang.ma_don_hang == ma)
        .order_by(ChiTietDonHang.ma)
    )
    return {
        **thong_tin_don_hang(don_hang),
        "chi_tiet": [
            {
                "ma_san_pham": dong.ma_san_pham,
                "ten": ten if ten is not None else "Đồ uống không còn tồn tại",
                "so_luong": dong.so_luong,
                "don_gia": float(dong.don_gia),
                "phan_tram_duong": dong.phan_tram_duong,
                "muc_da": dong.muc_da,
                "ghi_chu": dong.ghi_chu,
                "thanh_tien": float(dong.don_gia * dong.so_luong)
            }
            for dong, ten in chi_tiet
        ]
    }


@router.patch("/orders/{ma}/payment")
def thanh_toan_don_hang(
    ma: int,
    du_lieu: DuLieuThanhToan,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    # Dùng cùng khóa với cập nhật trạng thái để thanh toán và hủy không chạy đồng thời.
    don_hang = csdl.get(DonHang, ma, with_for_update=True)
    if don_hang is None:
        raise HTTPException(404, "Không tìm thấy đơn hàng")
    if don_hang.trang_thai == "cancelled":
        raise HTTPException(409, "Đơn hàng đã hủy, không thể thanh toán")
    if don_hang.trang_thai_thanh_toan == "paid":
        raise HTTPException(409, "Đơn hàng đã được thanh toán")

    don_hang.phuong_thuc_thanh_toan = du_lieu.phuong_thuc
    don_hang.trang_thai_thanh_toan = "paid"
    don_hang.ngay_thanh_toan = datetime.now(timezone.utc).replace(tzinfo=None)
    csdl.commit()
    csdl.refresh(don_hang)

    return {
        "thong_bao": "Thanh toán thành công",
        "ma": don_hang.ma,
        "tong_tien": float(don_hang.tong_tien),
        "phuong_thuc": don_hang.phuong_thuc_thanh_toan,
        "trang_thai_thanh_toan": don_hang.trang_thai_thanh_toan,
        "ngay_thanh_toan": don_hang.ngay_thanh_toan.isoformat()
    }
