from controller.database import Database
from controller.login import LoginManager
from controller.webserver import WebServer
from logging import getLogger
from util.logging_configurator import LoggingConfigurator
from util.paths import ROOT
import os

logger = getLogger("main")


if __name__ == "__main__":
    #================================================================================
    # Init all Components
    #================================================================================
    logging_configurator = LoggingConfigurator(
                file_path=os.path.join(ROOT, "logs", "log.txt"),
                level="INFO")
    database = Database()
    login_manager = LoginManager(database)
    web_server = WebServer(login_manager)

    #================================================================================
    # Start Logger
    #================================================================================
    logging_configurator.start()

    #================================================================================
    # Start App Components
    #================================================================================
    logger.info("Starting Login Manager")
    login_manager.start()

    logger.info("Starting WebServer")
    web_server.start()

    logger.info("Starting Database")
    database.start()
