import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()
duong_dan_csdl = os.getenv("DATABASE_URL", "sqlite:///./cafe.db")
tham_so_ket_noi = {"connect_args": {"check_same_thread": False}} if duong_dan_csdl.startswith("sqlite") else {}
bo_may_csdl = create_engine(duong_dan_csdl, **tham_so_ket_noi)
PhienLamViec = sessionmaker(bind=bo_may_csdl, autoflush=False, autocommit=False)

class CoSo(DeclarativeBase):
    pass

def lay_csdl():
    phien = PhienLamViec()
    try:
        yield phien
    finally:
        phien.close()
