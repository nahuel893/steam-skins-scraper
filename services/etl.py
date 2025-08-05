from db.database import DataBase
from scrapers.steam import SteamAPIMarket
from core.loggin_config import logger

class ETLManager:
    def __init__(self, db: DataBase):

        # Set database instance
        self.db = db

        # Scrapers
        self.steam_scraper = SteamAPIMarket()
    
        logger.info("ETLManager initialized with database and scrapers.")

    def update_prices(self):
        pass

    def insert_items(self):
        items = self.steam_scraper.get_list_items()
        print("Items obtenidos: ", items[:10])

