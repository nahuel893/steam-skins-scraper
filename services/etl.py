from db.database import DataBase
from db.models import Item, Price
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
        # First obtain items in db 
        current_items = self.db.get_items()
        current_items = [item.hash_name for item in current_items]

        steam_items = self.steam_scraper.get_list_items()

        # Filter new items that are not in the current items
        new  = [item for item in steam_items if item["hash_name"] not in current_items]

        # Convert new items to Item model
        new_items = [Item(
            hash_name=item["hash_name"],
            type_=item["type_"],
            classid=item["classid"],
            instanceid=item["instanceid"],
            imagehash=item["imagehash"],
            tradable=item["tradable"]
        ) for item in new]

        self.db.bulk_insert_items(new_items)
        n = len(new_items)
        logger.info(f"Inserted {n} new items into the database.")
        return n

