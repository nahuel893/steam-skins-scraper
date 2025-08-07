from db.database import DataBase
from core.loggin_config import logger
from services.etl import ETLManager

# steamid = "76561198102151621"
# data_inventory = DataInventory(steamid)
# data_inventory.transform_data()

# data_inventory.show_data()
# data_inventory.to_excel()

logger.info("Starting the database initialization...")

db = DataBase()
db.init_db()
logger.info("Database initialized successfully.")

etl = ETLManager(db)
etl.insert_items()

logger.info("ETL process completed successfully. All new items have been inserted into the database.")

db.close()
logger.info("Database connection closed.")