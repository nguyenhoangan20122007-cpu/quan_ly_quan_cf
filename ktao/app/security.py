import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt
from pwdlib import PasswordHash

load_dotenv()

# Cau hinh bao mat
def lay_khoa_bi_mat() -> str:
    gia_tri = os.getenv("SECRET_KEY")

    if not gia_tri:
        raise RuntimeError(
            "Chua cau hinh SECRET_KEY trong file .env"
        )

    return gia_tri


khoa_bi_mat: str = lay_khoa_bi_mat()

thuat_toan = "HS256"
thoi_gian_het_han = 60

# Cong cu bam mat khau
bo_bam_mat_khau = PasswordHash.recommended()


# Bam mat khau truoc khi luu vao MySQL
def bam_mat_khau(mat_khau: str) -> str:
    return bo_bam_mat_khau.hash(mat_khau)


# Kiem tra mat khau khi dang nhap
def kiem_tra_mat_khau(
    mat_khau: str,
    mat_khau_bam: str
) -> bool:
    return bo_bam_mat_khau.verify(
        mat_khau,
        mat_khau_bam
    )


# Tao access token
def tao_access_token(du_lieu: dict) -> str:
    noi_dung = du_lieu.copy()

    thoi_gian = datetime.now(timezone.utc) + timedelta(
        minutes=thoi_gian_het_han
    )

    noi_dung.update({
        "exp": thoi_gian
    })

    token = jwt.encode(
        noi_dung,
        khoa_bi_mat,
        algorithm=thuat_toan
    )

    return token