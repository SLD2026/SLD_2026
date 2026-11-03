from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import sys
from pathlib import Path

# Perbaiki path agar bisa membaca config.py di root
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Camera(Base):
    __tablename__ = "cameras"
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    rtsp_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    roi_polygon = Column(Text, nullable=True)

class ViolationLog(Base):
    __tablename__ = "violation_logs"
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    identified_person_id = Column(String(100), default="Tidak Dikenali")
    similarity_score = Column(String(20), default="0.0")
    image_proof_path = Column(String(255), nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)