from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Skin(Base):
    __tablename__ = "skins"
    id = Column(Integer, primary_key=True)
    hash_name = Column(String, unique=True, index=True)
    type = Column(String)  # Ej: "Classified Rifle"
    classid = Column(String)  # IDs de Steam
    instanceid = Column(String)
    imageurl = Column(String)  # URL del 

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    skin_id = Column(Integer, ForeignKey("skins.id"))
    market = Column(String)  # Ej: "Steam", "Buff", "Skinport"
    price = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
