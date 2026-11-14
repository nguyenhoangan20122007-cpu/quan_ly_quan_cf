from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

class DuLieuDanhMuc(BaseModel):
    ten: str = Field(min_length=1, max_length=100)

class DuLieuSanPham(BaseModel):
    ma_danh_muc: int
    ten: str = Field(min_length=1, max_length=120)
    gia: Decimal = Field(gt=0)
    mo_ta: str | None = None
    hinh_anh: str | None = Field(default=None, max_length=500)

class DuLieuChiTiet(BaseModel):
    ma_san_pham: int
    so_luong: int = Field(ge=1)
    phan_tram_duong: int = Field(default=100, ge=0, le=100)
    muc_da: str = Field(default="normal", pattern="^(none|less|normal|more)$")
    ghi_chu: str | None = Field(default=None, max_length=255)

class DuLieuDonHang(BaseModel):
    ma_khach_hang: int | None = None
    chi_tiet: list[DuLieuChiTiet] = Field(min_length=1)
class DuLieuKhachHang(BaseModel):
    ten: str = Field(min_length=1, max_length=100)
    so_dien_thoai: str | None = Field(default=None, max_length=20)


class DuLieuTrangThaiDanhMuc(BaseModel):
    trang_thai: Literal["active", "inactive"]


class DuLieuTrangThaiSanPham(BaseModel):
    trang_thai: Literal["available", "unavailable"]
