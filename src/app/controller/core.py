from app.controller.database import Database
from app.controller.router import Router
from app.controller.login import LoginManager
from app.util.logging_configurator import LoggingConfigurator
from app.util.resource_manager import ResourceManager
from app.view.templates import TemplateBuilder
from logging import getLogger
import os
import time
from app.debug.server import Server

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

logger = getLogger("core")


class ApplicationCore(object):
    """Main component aggregator and Business logic"""

    #================================================================================
    # Construction
    #================================================================================
    def __init__(self):
        self.resource_manager = None
        self.logging_configurator = None
        self.database = None
        self.resume_builder = None
        self.template_builder = None

    def start(self):
        """Start the app"""
        # Start the logger so we can begin logging ----------------------------------
        logging_configurator = \
                LoggingConfigurator(file_path=os.path.join(ROOT, "logs", "log.txt"),
                                    level="INFO")
        logging_configurator.start()

        # Init all Components -------------------------------------------------------
        self.resource_manager = ResourceManager()
        self.template_builder = TemplateBuilder(self.resource_manager)
        self.database = Database(self.resource_manager)
        self.login_manager = LoginManager(self.database, self.resource_manager)
        self.router = Router(self.resource_manager,
                             self.template_builder,
                             self.login_manager)
        self.debug_server = Server(self.router)

        # Start all Components ------------------------------------------------------
        self._start_component("Template Builder", self.template_builder)

        self._start_component("Login Manager", self.login_manager)

        self._start_component("Database", self.database)

        self._start_component("Router", self.router)

        self._start_component("Debug Server", self.debug_server)

        # Main loop -----------------------------------------------------------------
        try:
            print "Ctrl+C to quit..."
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print "Interrupt received... shutting down"
            os._exit(0)

    #================================================================================
    # Internal
    #================================================================================
    def _start_component(self, component_name, component):
        logger.info("Starting %s...", component_name)
        component.start()
        logger.info("...%s complete.", component_name)
