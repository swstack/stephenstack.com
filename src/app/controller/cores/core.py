from logging import getLogger
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                     "..", "..", "..", ".."))

logger = getLogger("core")


class ApplicationCoreABC(object):
    """Abstract Base Class for the main logic core component"""

    #===========================================================================
    # Construction
    #===========================================================================
    def __init__(self):

        # Components that may be started
        self.platform = None
        self.resource_manager = None
        self.logging_configurator = None
        self.database = None
        self.resume_builder = None
        self.template_builder = None
        self.debug_server = None

    def start(self):
        logger.error("Application Core Base Class is not meant to be"
                     "started directly, please subclass")

    #===========================================================================
    # Internal
    #===========================================================================
    def _start_component(self, component_name, component):
        logger.info("Starting %s...", component_name)
        component.start()
        logger.info("...%s complete.", component_name)
