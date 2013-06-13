from controller.webserver import WebServer
from util.logging_configurator import LoggingConfigurator
from logging import getLogger
import os
from util.paths import ROOT

logger = getLogger("main")


if __name__ == "__main__":
    # Instantiate all components
    logging_configurator = LoggingConfigurator(
                file_path=os.path.join(ROOT, "logs", "log.txt"),
                level="INFO")
    web_server = WebServer()

    # Start all components
    logging_configurator.start()

    logger.info("Starting WebServer")
    web_server.start()
