import os
import pkg_resources


class ResourceManager(object):
    """Provides paths for use by other components (abstraction layer)"""

    def __init__(self):
        # resource_filename will extract to some temporary location (cache)
        # this can be controlled via the pkg_resources API if needed
        self.resource_root = pkg_resources.resource_filename("app", "resources")

    def get_fs_resource_root(self):
        """Get the root for all filesystem-based resources"""
        return os.path.abspath(self.resource_root)

    def get_fs_resource_path(self, resource_name):
        """Get the path to a particular resource group"""
        return os.path.join(self.get_fs_resource_root(), resource_name)
