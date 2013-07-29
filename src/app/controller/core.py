from app.controller.database import Database
from app.controller.login import LoginManager
from app.controller.resume import ResumeBuilder
from app.controller.routes import Router
from app.controller.server import Server
from app.util.logging_configurator import LoggingConfigurator
from app.util.resource_manager import ResourceManager
from app.view.templates import TemplateBuilder
from logging import getLogger
import os
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

logger = getLogger("core")


class ApplicationCore(object):
    """Main component aggregator and Business logic"""

    def __init__(self):
        self.resource_manager = None
        self.logging_configurator = None
        self.database = None
        self.resume_builder = None
        self.template_builder = None
        self.router = None

    #================================================================================
    # Main start method, every component in the system should have one
    #================================================================================
    def start(self):
        """Start the app"""
        # Start the logger so we can begin logging ----------------------------------
        logging_configurator = \
                LoggingConfigurator(file_path=os.path.join(ROOT, "logs", "log.txt"),
                                    level="INFO")
        logging_configurator.start()

        # Init all Components -------------------------------------------------------
        self.router = Router()
        self.resource_manager = ResourceManager()
        self.template_builder = TemplateBuilder(self.resource_manager)
        self.resume_builder = ResumeBuilder(self.resource_manager)
        self.database = Database(self.resource_manager)
        self.login_manager = LoginManager(self.database, self.resource_manager)
        self.server = Server(self.resource_manager,
                             self.router,
                             self.template_builder,
                             self.login_manager,
                             self.resume_builder)

        # Start all Components ------------------------------------------------------
        self._start_component("Template Builder", self.template_builder)

        self._start_component("Login Manager", self.login_manager)

        self._start_component("Resume Builder", self.resume_builder)

        self._start_component("Database", self.database)

        self._start_component("Server", self.server)

        # Main loop -----------------------------------------------------------------
        try:
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
