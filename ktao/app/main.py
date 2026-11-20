from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import delete, select, func
from sqlalchemy.exc import IntegrityError

from app.database import CoSo, bo_may_csdl, lay_csdl
from app.models import (
    NguoiDung,
    DanhMuc,
    SanPham,
    DonHang,
    ChiTietDonHang,
    KhachHang
)
from app.schemas import (
    DuLieuDanhMuc,
    DuLieuSanPham,
    DuLieuKhachHang,
    DuLieuTrangThaiDanhMuc,
    DuLieuTrangThaiSanPham
)
from app.auth import router as auth_router
from app.dependencies import yeu_cau_admin, yeu_cau_nhan_vien
from app.tao_don_hang import router as tao_don_hang_router
from app.thanh_toan_lich_su_don import router as thanh_toan_lich_su_don_router


@asynccontextmanager
async def vong_doi(ung_dung: FastAPI):
    CoSo.metadata.create_all(bind=bo_may_csdl)
    yield


ung_dung = FastAPI(
    title="API Quản lý quán cà phê",
    version="0.1.0",
    lifespan=vong_doi
)

ung_dung.include_router(auth_router)
ung_dung.include_router(tao_don_hang_router)
ung_dung.include_router(thanh_toan_lich_su_don_router)


# Trang chu
@ung_dung.get("/")
def trang_chu():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@ung_dung.get("/static/tao_don_hang.js", include_in_schema=False)
def javascript_tao_don_hang():
    return FileResponse(
        Path(__file__).parent / "static" / "tao_don_hang.js",
        media_type="text/javascript"
    )


@ung_dung.get("/static/thanh_toan_lich_su_don.js", include_in_schema=False)
def javascript_thanh_toan_lich_su_don():
    return FileResponse(
        Path(__file__).parent / "static" / "thanh_toan_lich_su_don.js",
        media_type="text/javascript"
    )


# Kiem tra server
@ung_dung.get("/health")
def kiem_tra():
    return {"trang_thai": "ok"}


# Xem danh muc: Admin va nhan vien
@ung_dung.get("/categories")
def xem_danh_muc(
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    return [
        {"ma": muc.ma, "ten": muc.ten, "trang_thai": muc.trang_thai}
        for muc in csdl.scalars(select(DanhMuc)).all()
    ]


# Them danh muc: Chi Admin
@ung_dung.post("/categories", status_code=201)
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


@ung_dung.put("/categories/{ma}")
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


@ung_dung.delete("/categories/{ma}")
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


@ung_dung.patch("/categories/{ma}/status")
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
@ung_dung.get("/products")
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
@ung_dung.post("/products", status_code=201)
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


@ung_dung.patch("/products/{ma}/status")
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


@ung_dung.put("/products/{ma}")
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


@ung_dung.delete("/products/{ma}")
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

from pydantic import BaseModel
from typing import Literal


class DuLieuTrangThai(BaseModel):
    trang_thai: Literal[
        "pending",
        "preparing",
        "completed",
        "cancelled"
    ]


@ung_dung.patch("/orders/{ma}/status")
def cap_nhat_trang_thai(
    ma: int,
    du_lieu: DuLieuTrangThai,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    don_hang = csdl.get(DonHang, ma, with_for_update=True)

    if don_hang is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy đơn hàng"
        )

    if du_lieu.trang_thai == "cancelled" and don_hang.trang_thai_thanh_toan == "paid":
        raise HTTPException(409, "Đơn đã thanh toán, không thể hủy trực tiếp")

    if don_hang.trang_thai in ("completed", "cancelled"):
        raise HTTPException(
            status_code=409,
            detail="Đơn hàng đã kết thúc, không thể thay đổi trạng thái"
        )

    trang_thai_moi = du_lieu.trang_thai

    chuyen_trang_thai_hop_le = {
        "pending": {"preparing", "cancelled"},
        "preparing": {"completed", "cancelled"}
    }

    if trang_thai_moi not in chuyen_trang_thai_hop_le.get(
        don_hang.trang_thai, set()
    ):
        raise HTTPException(
            status_code=400,
            detail="Chuyển trạng thái đơn hàng không hợp lệ"
        )

    don_hang.trang_thai = trang_thai_moi

    csdl.commit()
    csdl.refresh(don_hang)

    return {
        "thong_bao": "Cập nhật trạng thái thành công",
        "ma_don_hang": don_hang.ma,
        "trang_thai": don_hang.trang_thai
    }


@ung_dung.get("/statistics")
def thong_ke_doanh_thu(
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    tong_san_pham = csdl.scalar(
        select(func.count(SanPham.ma))
    ) or 0

    tong_don_hang = csdl.scalar(
        select(func.count(DonHang.ma))
    ) or 0

    don_hoan_thanh = csdl.scalar(
        select(func.count(DonHang.ma)).where(
            DonHang.trang_thai == "completed"
        )
    ) or 0

    don_da_huy = csdl.scalar(
        select(func.count(DonHang.ma)).where(
            DonHang.trang_thai == "cancelled"
        )
    ) or 0

    doanh_thu = csdl.scalar(
        select(func.sum(DonHang.tong_tien)).where(
            DonHang.trang_thai == "completed"
        )
    ) or 0

    return {
        "tong_san_pham": tong_san_pham,
        "tong_don_hang": tong_don_hang,
        "don_hoan_thanh": don_hoan_thanh,
        "don_da_huy": don_da_huy,
        "doanh_thu": float(doanh_thu)
    }
@ung_dung.get("/customers")
def xem_khach_hang(
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    danh_sach = csdl.scalars(
        select(KhachHang).order_by(KhachHang.ma.desc())
    ).all()

    return [
        {
            "ma": kh.ma,
            "ten": kh.ten,
            "so_dien_thoai": kh.so_dien_thoai
        }
        for kh in danh_sach
    ]

@ung_dung.post("/customers", status_code=201)
def them_khach_hang(
    du_lieu: DuLieuKhachHang,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    khach_hang = KhachHang(
        ten=du_lieu.ten.strip(),
        so_dien_thoai=du_lieu.so_dien_thoai
    )

    csdl.add(khach_hang)
    csdl.commit()
    csdl.refresh(khach_hang)

    return {
        "thong_bao": "Thêm khách hàng thành công",
        "ma": khach_hang.ma,
        "ten": khach_hang.ten,
        "so_dien_thoai": khach_hang.so_dien_thoai
    }


@ung_dung.put("/customers/{ma}")
def sua_khach_hang(
    ma: int,
    du_lieu: DuLieuKhachHang,
    csdl: Session = Depends(lay_csdl),
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    khach_hang = csdl.get(KhachHang, ma)

    if khach_hang is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy khách hàng"
        )

    khach_hang.ten = du_lieu.ten.strip()
    khach_hang.so_dien_thoai = du_lieu.so_dien_thoai

    csdl.commit()
    csdl.refresh(khach_hang)

    return {
        "thong_bao": "Sửa khách hàng thành công",
        "ma": khach_hang.ma,
        "ten": khach_hang.ten,
        "so_dien_thoai": khach_hang.so_dien_thoai
    }


def khoang_ngay_thong_ke(
    tu_ngay: str | None = Query(default=None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    den_ngay: str | None = Query(default=None, description="Ngày kết thúc (YYYY-MM-DD)")
):
    mui_gio_vn = ZoneInfo("Asia/Ho_Chi_Minh")
    hom_nay = datetime.now(mui_gio_vn).date()

    try:
        ngay_bat_dau = date.fromisoformat(tu_ngay) if tu_ngay is not None else hom_nay.replace(day=1)
        ngay_ket_thuc = date.fromisoformat(den_ngay) if den_ngay is not None else hom_nay
        if (
            (tu_ngay is not None and tu_ngay != ngay_bat_dau.isoformat())
            or (den_ngay is not None and den_ngay != ngay_ket_thuc.isoformat())
        ):
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Ngày phải có định dạng YYYY-MM-DD"
        ) from None

    if ngay_bat_dau > ngay_ket_thuc:
        raise HTTPException(
            status_code=400,
            detail="Ngày bắt đầu không được lớn hơn ngày kết thúc"
        )

    # created_at lưu UTC không kèm múi giờ. Cận trên là đầu ngày kế tiếp.
    mot_ngay = timedelta(days=1)
    try:
        bat_dau_vn = datetime.combine(ngay_bat_dau, datetime.min.time(), mui_gio_vn)
        ket_thuc_vn = datetime.combine(ngay_ket_thuc + mot_ngay, datetime.min.time(), mui_gio_vn)
        bat_dau_utc = bat_dau_vn.astimezone(timezone.utc).replace(tzinfo=None)
        ket_thuc_utc = ket_thuc_vn.astimezone(timezone.utc).replace(tzinfo=None)
    except OverflowError:
        raise HTTPException(status_code=400, detail="Khoảng ngày vượt ngoài phạm vi hỗ trợ") from None

    return ngay_bat_dau, ngay_ket_thuc, mui_gio_vn, (
        DonHang.trang_thai == "completed",
        DonHang.ngay_tao >= bat_dau_utc,
        DonHang.ngay_tao < ket_thuc_utc
    )


def tong_hop_doanh_thu_theo_ngay(csdl: Session, mui_gio_vn: ZoneInfo, dieu_kien):
    cac_don = csdl.execute(
        select(DonHang.ngay_tao, DonHang.tong_tien)
        .where(*dieu_kien)
        .execution_options(yield_per=1000)
    )

    thong_ke = {}
    gia_tri_rong = (0, Decimal("0"))
    for ngay_tao, tong_tien in cac_don:
        ngay = ngay_tao.replace(tzinfo=timezone.utc).astimezone(mui_gio_vn).date()
        so_don, doanh_thu = thong_ke.get(ngay, gia_tri_rong)
        thong_ke[ngay] = (so_don + 1, doanh_thu + tong_tien)

    return thong_ke


@ung_dung.get("/statistics/revenue", tags=["Thống kê"], dependencies=[Depends(yeu_cau_admin)])
def thong_ke_doanh_thu_theo_ngay(
    csdl: Session = Depends(lay_csdl),
    khoang_ngay = Depends(khoang_ngay_thong_ke)
):
    ngay_bat_dau, ngay_ket_thuc, mui_gio_vn, dieu_kien = khoang_ngay
    thong_ke = tong_hop_doanh_thu_theo_ngay(csdl, mui_gio_vn, dieu_kien)
    tong_ly_ban = csdl.scalar(
        select(func.coalesce(func.sum(ChiTietDonHang.so_luong), 0))
        .join(DonHang, ChiTietDonHang.ma_don_hang == DonHang.ma)
        .where(*dieu_kien)
    )

    chi_tiet = []
    tong_so_don = 0
    tong_doanh_thu = Decimal("0")
    gia_tri_rong = (0, Decimal("0"))
    mot_ngay = timedelta(days=1)
    ngay = ngay_bat_dau
    while ngay <= ngay_ket_thuc:
        so_don, doanh_thu = thong_ke.get(ngay, gia_tri_rong)
        chi_tiet.append({
            "ngay": ngay.isoformat(),
            "so_don": so_don,
            "doanh_thu": float(doanh_thu)
        })
        tong_so_don += so_don
        tong_doanh_thu += doanh_thu
        ngay += mot_ngay

    return {
        "tu_ngay": ngay_bat_dau.isoformat(),
        "den_ngay": ngay_ket_thuc.isoformat(),
        "tong_so_don": tong_so_don,
        "tong_don_hang": tong_so_don,
        "tong_doanh_thu": float(tong_doanh_thu),
        "tong_ly_ban": int(tong_ly_ban),
        "chi_tiet": chi_tiet
    }


@ung_dung.get("/statistics/top-products", tags=["Thống kê"], dependencies=[Depends(yeu_cau_admin)])
def thong_ke_do_uong_ban_chay(
    csdl: Session = Depends(lay_csdl),
    khoang_ngay = Depends(khoang_ngay_thong_ke)
):
    _, _, _, dieu_kien = khoang_ngay
    tong_so_luong = func.sum(ChiTietDonHang.so_luong)
    ket_qua = csdl.execute(
        select(SanPham.ma, SanPham.ten, tong_so_luong)
        .join(ChiTietDonHang, ChiTietDonHang.ma_san_pham == SanPham.ma)
        .join(DonHang, ChiTietDonHang.ma_don_hang == DonHang.ma)
        .where(*dieu_kien)
        .group_by(SanPham.ma, SanPham.ten)
        .order_by(tong_so_luong.desc(), SanPham.ma)
        .limit(5)
    )
    return [{"ma": ma, "ten": ten, "so_luong": int(so_luong)} for ma, ten, so_luong in ket_qua]


@ung_dung.get("/statistics/daily", tags=["Thống kê"], dependencies=[Depends(yeu_cau_admin)])
def doanh_thu_theo_ngay(
    csdl: Session = Depends(lay_csdl),
    khoang_ngay = Depends(khoang_ngay_thong_ke)
):
    _, _, mui_gio_vn, dieu_kien = khoang_ngay
    thong_ke = tong_hop_doanh_thu_theo_ngay(csdl, mui_gio_vn, dieu_kien)
    return [
        {"ngay": ngay.isoformat(), "doanh_thu": float(doanh_thu)}
        for ngay, (_, doanh_thu) in sorted(thong_ke.items())
    ]
