import logging


class LoggerConfig:
    """
    A class to configure and provide a logger instance.
    """

    @staticmethod
    def get_logger(name=__name__, log_file="skinspock_api.log", level=logging.INFO):
        """
        Configures and returns a logger instance.
        Args:
            name (str): The name of the logger.
            log_file (str): The file where logs will be written.
            level (int): The logging level.
        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        # Stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        # Add handlers to the logger
        if not logger.handlers:  # Avoid adding handlers multiple times
            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)

        return logger


# Initialize the logger
logger = LoggerConfig.get_logger()