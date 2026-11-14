from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import lay_csdl
from app.models import NguoiDung
from app.security import kiem_tra_mat_khau, tao_access_token
from app.dependencies import lay_nguoi_dung_hien_tai


# Tao router xac thuc
router = APIRouter(
    prefix="/auth",
    tags=["Xac thuc"]
)


# API dang nhap
@router.post("/login")
def dang_nhap(
    du_lieu: OAuth2PasswordRequestForm = Depends(),
    csdl: Session = Depends(lay_csdl)
):
    # Tim tai khoan trong MySQL
    nguoi_dung = csdl.query(NguoiDung).filter(
        NguoiDung.ten_dang_nhap == du_lieu.username
    ).first()

    # Kiem tra tai khoan
    if nguoi_dung is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ten dang nhap hoac mat khau khong dung"
        )

    # Kiem tra mat khau
    try:
        mat_khau_hop_le = kiem_tra_mat_khau(
            du_lieu.password,
            nguoi_dung.mat_khau_bam
        )
    except (ValueError, TypeError):
        mat_khau_hop_le = False

    if not mat_khau_hop_le:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ten dang nhap hoac mat khau khong dung"
        )

    # Tao JWT
    token = tao_access_token({
        "sub": str(nguoi_dung.ma)
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "vai_tro": nguoi_dung.vai_tro,
        "ten_dang_nhap": nguoi_dung.ten_dang_nhap
    }


# API dang xuat
@router.post("/logout")
def dang_xuat(
    nguoi_dung: NguoiDung = Depends(lay_nguoi_dung_hien_tai)
):
    return {
        "thong_bao": "Yeu cau dang xuat thanh cong. Hay xoa token o giao dien."
    }


# API xem thong tin tai khoan
@router.get("/me")
def thong_tin_tai_khoan(
    nguoi_dung: NguoiDung = Depends(lay_nguoi_dung_hien_tai)
):
    return {
        "ma": nguoi_dung.ma,
        "ten_dang_nhap": nguoi_dung.ten_dang_nhap,
        "vai_tro": nguoi_dung.vai_tro
    }


from app.dependencies import yeu_cau_admin, yeu_cau_nhan_vien


# API chi danh cho Admin
@router.get("/admin")
def kiem_tra_admin(
    nguoi_dung: NguoiDung = Depends(yeu_cau_admin)
):
    return {
        "thong_bao": "Ban co quyen Admin",
        "ten_dang_nhap": nguoi_dung.ten_dang_nhap,
        "vai_tro": nguoi_dung.vai_tro
    }


# API danh cho Admin va nhan vien
@router.get("/staff")
def kiem_tra_nhan_vien(
    nguoi_dung: NguoiDung = Depends(yeu_cau_nhan_vien)
):
    return {
        "thong_bao": "Ban co quyen truy cap",
        "ten_dang_nhap": nguoi_dung.ten_dang_nhap,
        "vai_tro": nguoi_dung.vai_tro
    }