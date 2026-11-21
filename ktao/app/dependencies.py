import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import lay_csdl
from app.models import NguoiDung
from app.security import khoa_bi_mat, thuat_toan


# Cau hinh xac thuc OAuth2
xac_thuc_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def ma_phien_nhan_vien(nguoi_dung: NguoiDung) -> str:
    # Mật khẩu đổi thì mã phiên đổi, kể cả khi đặt lại cùng một mật khẩu.
    return hmac.digest(khoa_bi_mat.encode(), nguoi_dung.mat_khau_bam.encode(), "sha256").hex()


# Lay thong tin nguoi dung hien tai
def lay_nguoi_dung_hien_tai(
    token: str = Depends(xac_thuc_oauth2),
    csdl: Session = Depends(lay_csdl)
):
    loi_xac_thuc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token khong hop le hoac da het han",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:
        # Giai ma JWT
        du_lieu = jwt.decode(
            token,
            khoa_bi_mat,
            algorithms=[thuat_toan]
        )

        # Lay ma nguoi dung trong token
        ma_nguoi_dung = du_lieu.get("sub")

        if ma_nguoi_dung is None:
            raise loi_xac_thuc

        ma_nguoi_dung = int(ma_nguoi_dung)

    except (JWTError, ValueError, TypeError):
        raise loi_xac_thuc

    # Tim tai khoan trong MySQL
    nguoi_dung = csdl.get(
        NguoiDung,
        ma_nguoi_dung
    )

    if nguoi_dung is None:
        raise loi_xac_thuc
    if nguoi_dung.trang_thai == "locked":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đã bị khóa")
    if nguoi_dung.vai_tro == "staff" and du_lieu.get("phien") != ma_phien_nhan_vien(nguoi_dung):
        raise loi_xac_thuc

    return nguoi_dung


# Kiem tra quyen Admin
def yeu_cau_admin(
    nguoi_dung: NguoiDung = Depends(
        lay_nguoi_dung_hien_tai
    )
):
    if nguoi_dung.vai_tro != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ban khong co quyen Admin"
        )

    return nguoi_dung


# Kiem tra quyen Admin hoac nhan vien
def yeu_cau_nhan_vien(
    nguoi_dung: NguoiDung = Depends(
        lay_nguoi_dung_hien_tai
    )
):
    if nguoi_dung.vai_tro not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ban khong co quyen truy cap"
        )

    return nguoi_dung