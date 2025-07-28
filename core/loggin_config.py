import logging
from logging.handlers import RotatingFileHandler
import os

# Crear carpeta logs si no existe
os.makedirs("logs", exist_ok=True)

# Configuración del logger principal
logger = logging.getLogger("steam_scraper")
logger.setLevel(logging.DEBUG)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Handler de log general (info y debug)
file_handler = RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=5)
file_handler.setLevel(logging.INFO)

# Handler de log de errores
error_handler = RotatingFileHandler("logs/errors.log", maxBytes=5_000_000, backupCount=5)
error_handler.setLevel(logging.ERROR)

# Formato de los logs
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Handler para consola (útil durante desarrollo)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Añadir handlers al logger principal
logger.addHandler(file_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)
