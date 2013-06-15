from controller.database import Database
from controller.webserver import WebServer
from logging import getLogger
from model.model import User
from util.logging_configurator import LoggingConfigurator
from util.paths import ROOT
import os

logger = getLogger("main")


if __name__ == "__main__":
    # Instantiate all components
    logging_configurator = LoggingConfigurator(
                file_path=os.path.join(ROOT, "logs", "log.txt"),
                level="INFO")
    web_server = WebServer()
    database = Database()

    # Start all components
    logging_configurator.start()

    logger.info("Starting WebServer")
    web_server.start()

    logger.info("Starting Database")
    database.start()

    db = database.get_session()

    print db.query(User).all()
