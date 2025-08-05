"""
Module for managing and transforming data from the various Steam skin APIs...
"""
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Item, Price
from sqlalchemy.exc import IntegrityError

class DataBase:
    DATA_BASE = "sqlite:///database.db"

    def __init__(self, appid: int = 730) -> None:
        self.engine = create_engine(self.DATA_BASE, echo=True)
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)
        self.session = None
    
    def init_db(self) -> None:
        """
        Inicializa la base de datos y crea las tablas si no existen.
        """
        Base.metadata.create_all(bind=self.engine)
        self.session = self.session_local()

    def add_item(self, hash_name: str, type_: str, classid: str, instanceid: str, imagehash: str, tradable: int, sell_price_text: str) -> None:
        """
        Agrega un skin a la base de datos.
        """
        item = Item(
            hash_name=hash_name,
            type_=type_,
            classid=classid,
            instanceid=instanceid,
            imagehash=imagehash,
            tradable=tradable,
        )
        self.session.add(item)

        # Si encuentra un error de integridad, hace rollback y retorna el skin existente para evitar duplicados
        # Esto es útil si el skin ya existe en la base de datos
        try:
            self.session.commit()
            self.session.refresh(item)
            return item
        
        except IntegrityError: # Cuando intentas ingresar un repetido (id o hashname)
            self.session.rollback()
            return self.session.query(Item).filter_by(hash_name=hash_name).first()
        
    def delete_item(self, hash_name: str) -> None:
        """       
        Elimina un skin de la base de datos.
        """

        item = self.session.query(Item).filter_by(hash_name=hash_name).first()
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False
    
    def add_price(self, item_id: int, market: str, price: float) -> None:
        """
        Agrega un precio a la base de datos.
        """

        self.session = price = Price(item_id=item_id, market=market, price=price)
        self.session.add(price)
        self.session.commit()

        return price
    
    def get_item(self, hash_name: str) -> Item:
        pass

    def get_items(self) -> list[Item]:
        """
        Obtiene todos los items de la base de datos.
        """
        return self.session.query(Item).all()
    
    def bulk_insert_items(self, items: list[Item]) -> None:
        """
        Inserta múltiples items en la base de datos.
        """
        self.session.bulk_save_objects(items)
        self.session.commit()

    def bulk_insert_prices(self, prices: list[Price]) -> None:
        pass

    def close(self) -> None:
        """
        Cierra la sesión de la base de datos.
        """

        if self.session:
            self.session.close()