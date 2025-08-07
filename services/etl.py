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
        # Obtain items in db 
        current_items = [item.hash_name for item in self.db.get_items()]
        # Obtain items from Steam API
        steam_items = self.steam_scraper.get_list_items()
        # Filter new items that are not in the current items
        new = [item for item in steam_items if item["hash_name"] not in current_items]
        # Convert new items to Item model
        new_items = [Item(
            hash_name=item["hash_name"],
            type_=item["asset_description"]["type"],
            classid=item["asset_description"]["classid"],
            instanceid=item["asset_description"]["instanceid"],
            imagehash=item["asset_description"]["icon_url"],
            tradable=item["asset_description"]["tradable"]
        ) for item in new]
        self.db.bulk_insert_items(new_items)
        n = len(new_items)
        logger.info(f"Inserted {n} new items into the database.")
        return n

