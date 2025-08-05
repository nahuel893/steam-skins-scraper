"""
Module for modeling the database schema for Steam skins and prices.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    hash_name = Column(String, unique=True, index=True)

    # "asset_description"
    type_ = Column(String)  # Ej: "Classified Rifle"
    classid = Column(String)  # IDs de Steam
    instanceid = Column(String)
    imagehash = Column(String)  # Hash of image
    tradable = Column(Integer)  # 1 si es comerciable, 0 si no

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    market = Column(String)  # Ej: "Steam", "Buff", "Skinport"
    price = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
