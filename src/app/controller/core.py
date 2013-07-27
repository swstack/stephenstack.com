from app.controller.database import Database
from app.controller.login import LoginManager
from app.controller.resume import ResumeBuilder
from app.controller.webserver import Webserver
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
        self._static_root = None

    #================================================================================
    # Main start method, every component in the system should have one
    #================================================================================
    def start(self):
        """Start the app"""
        #============================================================================
        # Start the logger so we can begin logging
        #============================================================================
        logging_configurator = \
                LoggingConfigurator(file_path=os.path.join(ROOT, "logs", "log.txt"),
                                    level="INFO")
        logging_configurator.start()

        #================================================================================
        # Init all Components
        #================================================================================
        self.resource_manager = ResourceManager()
        self.template_builder = TemplateBuilder(self.resource_manager)
        self.resume_builder = ResumeBuilder(self.resource_manager)
        self.database = Database(self.resource_manager)
        self.login_manager = LoginManager(self.database, self.resource_manager)
        self.webserver = Webserver(self, self.resource_manager)

        #================================================================================
        # Start all Components
        #================================================================================
        self._start_component("Template Builder", self.template_builder)

        self._start_component("Login Manager", self.login_manager)

        self._start_component("Resume Builder", self.resume_builder)

        self._start_component("Database", self.database)

        self._start_component("Webserver", self.webserver)

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print "Interrupt received... shutting down"
            os._exit(0)

    #================================================================================
    # Private
    #================================================================================
    def _start_component(self, component_name, component):
        logger.info("Starting %s...", component_name)
        component.start()
        logger.info("...%s complete.", component_name)

    #================================================================================
    # Public
    #================================================================================
    def get_static_root(self):
        """Return path to the static root for the http webserver, caching the
        value to reduce cpu cycles"""
        if not self._static_root:
            self._static_root = self.resource_manager.get_fs_resource_root()
        return self._static_root

    def get_index(self, **template_vars):
#        template_vars.update(resume=self.resume_builder.get_resume())
        template_vars.update(CLIENT_ID=unicode(self.login_manager.get_client_id()))
        return self.template_builder.get_index(template_vars)

    def login(self, username, password):
        if self.login_manager.login(username, password):
            return True
        return False
