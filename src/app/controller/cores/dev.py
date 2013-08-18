from app.controller.cores.core import ApplicationCoreABC, ROOT
from app.controller.database import Database
from app.controller.login import LoginManager
from app.controller.router import Router
from app.debug.server import Server
from app.util.logging_configurator import LoggingConfigurator
from app.util.platform import LinuxPlatform
from app.util.resource_manager import ResourceManager
from app.view.templates import TemplateBuilder
import os
import time


class DevCore(ApplicationCoreABC):
    """Core used for local development purposes"""

    def start(self):
        """Start the app"""
        # Start the logger so we can begin logging -----------------------------
        logging_configurator = \
                LoggingConfigurator(file_path=os.path.join(ROOT, "logs",
                                                           "log.txt"),
                                    level="INFO")
        logging_configurator.start()

        # Init all Components --------------------------------------------------
        self.platform = LinuxPlatform()
        self.resource_manager = ResourceManager()
        self.template_builder = TemplateBuilder(self.resource_manager)
        self.database = Database(self.resource_manager)
        self.login_manager = LoginManager(self.database,
                                          self.resource_manager,
                                          self.platform)
        self.router = Router(self.resource_manager,
                             self.template_builder,
                             self.login_manager,
                             self.database,
                             self.platform)
        self.debug_server = Server(self.router)

        # Start all Components -------------------------------------------------
        self._start_component("Linux Platform", self.platform)

        self._start_component("Template Builder", self.template_builder)

        self._start_component("Login Manager", self.login_manager)

        self._start_component("Database", self.database)

        self._start_component("Router", self.router)

        self._start_component("Debug Server", self.debug_server)

        # Main loop ------------------------------------------------------------
        try:
            print "Ctrl+C to quit..."
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print "Interrupt received... shutting down"
            os._exit(0)
