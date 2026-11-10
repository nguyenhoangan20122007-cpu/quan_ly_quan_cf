from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import CoSo, bo_may_csdl, lay_csdl
from app.models import DanhMuc, SanPham, DonHang, ChiTietDonHang, KhachHang
from app.schemas import DuLieuDanhMuc, DuLieuSanPham, DuLieuDonHang

@asynccontextmanager
async def vong_doi(ung_dung: FastAPI):
    CoSo.metadata.create_all(bind=bo_may_csdl)
    yield

ung_dung = FastAPI(title="API Quản lý quán cà phê", version="0.1.0", lifespan=vong_doi)

@ung_dung.get("/")
def trang_chu():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

@ung_dung.get("/health")
def kiem_tra():
    return {"trang_thai": "ok"}

@ung_dung.get("/categories")
def xem_danh_muc(csdl: Session = Depends(lay_csdl)):
    return [{"ma": muc.ma, "ten": muc.ten} for muc in csdl.scalars(select(DanhMuc)).all()]

@ung_dung.post("/categories", status_code=201)
def them_danh_muc(du_lieu: DuLieuDanhMuc, csdl: Session = Depends(lay_csdl)):
    if csdl.scalar(select(DanhMuc).where(DanhMuc.ten == du_lieu.ten)):
        raise HTTPException(409, "Danh mục đã tồn tại")
    danh_muc = DanhMuc(ten=du_lieu.ten)
    csdl.add(danh_muc)
    csdl.commit()
    csdl.refresh(danh_muc)
    return {"ma": danh_muc.ma, "ten": danh_muc.ten}

@ung_dung.get("/products")
def xem_san_pham(csdl: Session = Depends(lay_csdl)):
    return [{"ma": sp.ma, "ma_danh_muc": sp.ma_danh_muc, "ten": sp.ten, "gia": float(sp.gia), "mo_ta": sp.mo_ta} for sp in csdl.scalars(select(SanPham)).all()]

@ung_dung.post("/products", status_code=201)
def them_san_pham(du_lieu: DuLieuSanPham, csdl: Session = Depends(lay_csdl)):
    if not csdl.get(DanhMuc, du_lieu.ma_danh_muc):
        raise HTTPException(404, "Không tìm thấy danh mục")
    san_pham = SanPham(**du_lieu.model_dump())
    csdl.add(san_pham)
    csdl.commit()
    csdl.refresh(san_pham)
    return {"ma": san_pham.ma, "ten": san_pham.ten, "gia": float(san_pham.gia)}

@ung_dung.post("/orders", status_code=201)
def tao_don_hang(du_lieu: DuLieuDonHang, csdl: Session = Depends(lay_csdl)):
    if du_lieu.ma_khach_hang is not None and not csdl.get(KhachHang, du_lieu.ma_khach_hang):
        raise HTTPException(404, "Không tìm thấy khách hàng")
    danh_sach_san_pham = {}
    for dong in du_lieu.chi_tiet:
        san_pham = csdl.get(SanPham, dong.ma_san_pham)
        if san_pham is None:
            raise HTTPException(404, f"Không tìm thấy sản phẩm {dong.ma_san_pham}")
        danh_sach_san_pham[dong.ma_san_pham] = san_pham
    don_hang = DonHang(ma_khach_hang=du_lieu.ma_khach_hang, trang_thai="pending", tong_tien=Decimal("0"))
    tong_tien = Decimal("0")
    for dong in du_lieu.chi_tiet:
        san_pham = danh_sach_san_pham[dong.ma_san_pham]
        don_hang.chi_tiet.append(ChiTietDonHang(ma_san_pham=san_pham.ma, so_luong=dong.so_luong,
            don_gia=san_pham.gia, phan_tram_duong=dong.phan_tram_duong,
            muc_da=dong.muc_da, ghi_chu=dong.ghi_chu))
        tong_tien += san_pham.gia * dong.so_luong
    don_hang.tong_tien = tong_tien
    csdl.add(don_hang)
    csdl.commit()
    csdl.refresh(don_hang)
    return {"ma": don_hang.ma, "trang_thai": don_hang.trang_thai, "tong_tien": float(don_hang.tong_tien)}

@ung_dung.get("/orders")
def xem_don_hang(csdl: Session = Depends(lay_csdl)):
    return [{"ma": don.ma, "trang_thai": don.trang_thai, "tong_tien": float(don.tong_tien), "ngay_tao": don.ngay_tao.isoformat()} for don in csdl.scalars(select(DonHang)).all()]
