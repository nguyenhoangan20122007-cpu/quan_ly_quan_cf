from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import lay_csdl
from app.dependencies import yeu_cau_admin, yeu_cau_nhan_vien
from app.models import ChiTietDonHang, DanhMuc, NguoiDung, SanPham
from app.schemas import (
    DuLieuDanhMuc,
    DuLieuSanPham,
    DuLieuTrangThaiDanhMuc,
    DuLieuTrangThaiSanPham
)


router = APIRouter()


# Xem danh muc: Admin va nhan vien
@router.get("/categories")
def xem_danh_muc(
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    return [
        {"ma": muc.ma, "ten": muc.ten, "trang_thai": muc.trang_thai}
        for muc in csdl.scalars(select(DanhMuc)).all()
    ]


# Them danh muc: Chi Admin
@router.post("/categories", status_code=201)
def them_danh_muc(
    du_lieu: DuLieuDanhMuc,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    if csdl.scalar(
        select(DanhMuc).where(DanhMuc.ten == du_lieu.ten)
    ):
        raise HTTPException(409, "Danh mục đã tồn tại")

    danh_muc = DanhMuc(ten=du_lieu.ten)

    csdl.add(danh_muc)
    csdl.commit()
    csdl.refresh(danh_muc)

    return {
        "ma": danh_muc.ma,
        "ten": danh_muc.ten
    }


@router.put("/categories/{ma}")
def sua_danh_muc(
    ma: int,
    du_lieu: DuLieuDanhMuc,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    danh_muc = csdl.get(DanhMuc, ma, with_for_update=True)
    if danh_muc is None:
        raise HTTPException(404, "Không tìm thấy danh mục")

    ten_moi = du_lieu.ten.strip()
    if not ten_moi:
        raise HTTPException(400, "Tên danh mục không được để trống")

    danh_muc_trung = csdl.scalar(
        select(DanhMuc.ma).where(DanhMuc.ten == ten_moi, DanhMuc.ma != ma)
    )
    if danh_muc_trung is not None:
        raise HTTPException(409, "Danh mục đã tồn tại")

    danh_muc.ten = ten_moi
    try:
        csdl.commit()
    except IntegrityError as loi:
        csdl.rollback()
        raise HTTPException(409, "Danh mục đã tồn tại") from loi

    return {
        "thong_bao": "Sửa danh mục thành công",
        "ma": ma,
        "ten": ten_moi
    }


@router.delete("/categories/{ma}")
def xoa_danh_muc(
    ma: int,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    if csdl.get(DanhMuc, ma) is None:
        raise HTTPException(404, "Không tìm thấy danh mục")

    ma_san_pham = csdl.scalar(
        select(SanPham.ma).where(SanPham.ma_danh_muc == ma).limit(1)
    )
    if ma_san_pham is not None:
        raise HTTPException(409, "Danh mục đang có đồ uống, không thể xóa")

    try:
        ket_qua = csdl.connection().execute(delete(DanhMuc).where(DanhMuc.ma == ma))
        if ket_qua.rowcount == 0:
            raise HTTPException(404, "Không tìm thấy danh mục")
        csdl.commit()
    except IntegrityError as loi:
        csdl.rollback()
        raise HTTPException(409, "Danh mục đang có đồ uống, không thể xóa") from loi

    return {"thong_bao": "Xóa danh mục thành công", "ma": ma}


@router.patch("/categories/{ma}/status")
def cap_nhat_trang_thai_danh_muc(
    ma: int,
    du_lieu: DuLieuTrangThaiDanhMuc,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    danh_muc = csdl.get(DanhMuc, ma)
    if danh_muc is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")

    danh_muc.trang_thai = du_lieu.trang_thai
    csdl.commit()
    csdl.refresh(danh_muc)

    return {
        "thong_bao": "Cập nhật trạng thái danh mục thành công",
        "ma": danh_muc.ma,
        "trang_thai": danh_muc.trang_thai
    }


# Xem san pham: Admin va nhan vien
@router.get("/products")
def xem_san_pham(
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    san_pham_va_trang_thai_danh_muc = csdl.execute(
        select(SanPham, DanhMuc.trang_thai).outerjoin(SanPham.danh_muc)
    )
    return [
        {
            "ma": sp.ma,
            "ma_danh_muc": sp.ma_danh_muc,
            "ten": sp.ten,
            "gia": float(sp.gia),
            "mo_ta": sp.mo_ta,
            "hinh_anh": sp.hinh_anh,
            "trang_thai": sp.trang_thai,
            "trang_thai_danh_muc": trang_thai_danh_muc
        }
        for sp, trang_thai_danh_muc in san_pham_va_trang_thai_danh_muc
    ]


# Them san pham: Chi Admin
@router.post("/products", status_code=201)
def them_san_pham(
    du_lieu: DuLieuSanPham,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    if not csdl.get(DanhMuc, du_lieu.ma_danh_muc):
        raise HTTPException(404, "Không tìm thấy danh mục")

    san_pham = SanPham(**du_lieu.model_dump())

    csdl.add(san_pham)
    csdl.commit()
    csdl.refresh(san_pham)

    return {
        "ma": san_pham.ma,
        "ten": san_pham.ten,
        "gia": float(san_pham.gia)
    }


@router.patch("/products/{ma}/status")
def cap_nhat_trang_thai_san_pham(
    ma: int,
    du_lieu: DuLieuTrangThaiSanPham,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    san_pham = csdl.get(SanPham, ma)
    if san_pham is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    san_pham.trang_thai = du_lieu.trang_thai
    csdl.commit()
    csdl.refresh(san_pham)

    return {
        "thong_bao": "Cập nhật trạng thái sản phẩm thành công",
        "ma": san_pham.ma,
        "trang_thai": san_pham.trang_thai
    }


@router.put("/products/{ma}")
def sua_san_pham(
    ma: int,
    du_lieu: DuLieuSanPham,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    san_pham = csdl.get(SanPham, ma)

    if san_pham is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy sản phẩm"
        )

    danh_muc = csdl.get(DanhMuc, du_lieu.ma_danh_muc)

    if danh_muc is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy danh mục"
        )

    san_pham.ten = du_lieu.ten
    san_pham.gia = du_lieu.gia
    san_pham.ma_danh_muc = du_lieu.ma_danh_muc
    san_pham.mo_ta = du_lieu.mo_ta
    if "hinh_anh" in du_lieu.model_fields_set:
        san_pham.hinh_anh = du_lieu.hinh_anh

    csdl.commit()
    csdl.refresh(san_pham)

    return {
        "thong_bao": "Cập nhật sản phẩm thành công",
        "ma": san_pham.ma,
        "ten": san_pham.ten,
        "gia": float(san_pham.gia),
        "ma_danh_muc": san_pham.ma_danh_muc,
        "mo_ta": san_pham.mo_ta
    }


@router.delete("/products/{ma}")
def xoa_san_pham(
    ma: int,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    san_pham = csdl.get(SanPham, ma)

    if san_pham is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy sản phẩm"
        )

    # Kiem tra san pham da duoc dat hang chua
    chi_tiet = csdl.scalar(
        select(ChiTietDonHang).where(
            ChiTietDonHang.ma_san_pham == ma
        )
    )

    if chi_tiet is not None:
        raise HTTPException(
            status_code=409,
            detail="Sản phẩm đã có trong đơn hàng, không thể xóa"
        )

    csdl.delete(san_pham)
    csdl.commit()

    return {
        "thong_bao": "Xóa sản phẩm thành công",
        "ma_san_pham": ma
    }
