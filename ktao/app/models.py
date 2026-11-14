from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import ForeignKey, String, Numeric, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import CoSo

class NguoiDung(CoSo):
    __tablename__ = "users"
    ma: Mapped[int] = mapped_column("id", primary_key=True)
    ten_dang_nhap: Mapped[str] = mapped_column("username", String(60), unique=True)
    mat_khau_bam: Mapped[str] = mapped_column("password_hash", String(255))
    vai_tro: Mapped[str] = mapped_column("role", String(20), default="staff")

class KhachHang(CoSo):
    __tablename__ = "customers"
    ma: Mapped[int] = mapped_column("id", primary_key=True)
    ten: Mapped[str] = mapped_column("name", String(100))
    so_dien_thoai: Mapped[str | None] = mapped_column("phone", String(20), nullable=True)

class DanhMuc(CoSo):
    __tablename__ = "categories"
    ma: Mapped[int] = mapped_column("id", primary_key=True)
    ten: Mapped[str] = mapped_column("name", String(100), unique=True)
    trang_thai: Mapped[str] = mapped_column("status", String(20), default="active")
    san_pham: Mapped[list["SanPham"]] = relationship(back_populates="danh_muc")

class SanPham(CoSo):
    __tablename__ = "products"
    ma: Mapped[int] = mapped_column("id", primary_key=True)
    ma_danh_muc: Mapped[int] = mapped_column("category_id", ForeignKey("categories.id"))
    ten: Mapped[str] = mapped_column("name", String(120))
    gia: Mapped[Decimal] = mapped_column("price", Numeric(12, 2))
    mo_ta: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    hinh_anh: Mapped[str | None] = mapped_column("image_url", String(500), nullable=True)
    trang_thai: Mapped[str] = mapped_column("status", String(20), default="available")
    danh_muc: Mapped[DanhMuc] = relationship(back_populates="san_pham")

class DonHang(CoSo):
    __tablename__ = "orders"
    ma: Mapped[int] = mapped_column("id", primary_key=True)
    ma_nhan_vien: Mapped[int | None] = mapped_column("user_id", ForeignKey("users.id"), nullable=True)
    ma_khach_hang: Mapped[int | None] = mapped_column("customer_id", ForeignKey("customers.id"), nullable=True)
    ngay_tao: Mapped[datetime] = mapped_column("created_at", DateTime, default=lambda: datetime.now(timezone.utc))
    trang_thai: Mapped[str] = mapped_column("status", String(20), default="pending")
    tong_tien: Mapped[Decimal] = mapped_column("total", Numeric(12, 2), default=0)
    chi_tiet: Mapped[list["ChiTietDonHang"]] = relationship(back_populates="don_hang", cascade="all, delete-orphan")

class ChiTietDonHang(CoSo):
    __tablename__ = "order_items"
    ma: Mapped[int] = mapped_column("id", primary_key=True)
    ma_don_hang: Mapped[int] = mapped_column("order_id", ForeignKey("orders.id"))
    ma_san_pham: Mapped[int] = mapped_column("product_id", ForeignKey("products.id"))
    so_luong: Mapped[int] = mapped_column("quantity", Integer)
    don_gia: Mapped[Decimal] = mapped_column("unit_price", Numeric(12, 2))
    phan_tram_duong: Mapped[int] = mapped_column("sugar_percent", Integer, default=100)
    muc_da: Mapped[str] = mapped_column("ice_level", String(20), default="normal")
    ghi_chu: Mapped[str | None] = mapped_column("note", String(255), nullable=True)
    don_hang: Mapped[DonHang] = relationship(back_populates="chi_tiet")
