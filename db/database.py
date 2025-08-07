"""
Module for managing and transforming data from the various Steam skin APIs...
"""
import pandas as pd
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base, Item, Price
from sqlalchemy.exc import IntegrityError
from core.config import config

class DataBase:
    def __init__(self, appid: int = None) -> None:
        self.appid = appid or config.steam_config["app_id"]
        self.engine = create_engine(
            config.database_url, 
            echo=False  # Controlado por configuración
        )
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)
        self.session = None

    def init_db(self) -> None:
        """
        Inicializa la base de datos y crea las tablas si no existen.
        """
        Base.metadata.create_all(bind=self.engine)
        self.session = self.session_local()

    def add_item(self, hash_name: str, type_: str, classid: str, instanceid: str, imagehash: str, tradable: int, sell_price_text: str = "") -> Item:
        """
        Agrega un skin a la base de datos usando context manager para manejo seguro.
        """
        with self.get_session() as session:
            item = Item(
                hash_name=hash_name,
                type_=type_,
                classid=classid,
                instanceid=instanceid,
                imagehash=imagehash,
                tradable=tradable,
            )
            try:
                session.add(item)
                session.flush()  # Para obtener el ID sin commit completo
                session.refresh(item)
                return item
            except IntegrityError:
                # Si ya existe, buscar y retornar el existente
                session.rollback()
                return session.query(Item).filter_by(hash_name=hash_name).first()
        
    def delete_item(self, hash_name: str) -> bool:
        """       
        Elimina un skin de la base de datos usando context manager.
        """
        with self.get_session() as session:
            item = session.query(Item).filter_by(hash_name=hash_name).first()
            if item:
                session.delete(item)
                return True
            return False

    def add_price(self, item_id: int, market: str, price: float) -> Price:
        """
        Agrega un precio a la base de datos usando context manager.
        """
        with self.get_session() as session:
            price_obj = Price(item_id=item_id, market=market, price=price)
            session.add(price_obj)
            session.flush()
            session.refresh(price_obj)
            return price_obj

    def get_item(self, hash_name: str) -> Item | None:
        """
        Obtiene un item específico por su hash_name.
        """
        with self.get_session() as session:
            return session.query(Item).filter_by(hash_name=hash_name).first()

    def get_items(self) -> list[Item]:
        """
        Obtiene todos los items de la base de datos usando context manager.
        """
        with self.get_session() as session:
            return session.query(Item).all()

    def bulk_insert_items(self, items: list[Item]) -> int:
        """
        Inserta múltiples items en la base de datos usando context manager.
        Retorna el número de items insertados.
        """
        if not items:
            return 0
            
        with self.get_session() as session:
            session.bulk_save_objects(items)
            return len(items)

    def bulk_insert_prices(self, prices: list[Price]) -> int:
        """
        Inserta múltiples precios en la base de datos usando context manager.
        Retorna el número de precios insertados.
        """
        if not prices:
            return 0
            
        with self.get_session() as session:
            session.bulk_save_objects(prices)
            return len(prices)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager que garantiza el manejo seguro de sesiones.
        Automáticamente hace commit en caso de éxito y rollback en caso de error.
        """
        session = self.session_local()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """
        Cierra la sesión de la base de datos.
        """
        if self.session:
            self.session.close()