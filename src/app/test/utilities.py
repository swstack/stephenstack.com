from app.util.resource_manager import ResourceManager


class MockResourceManager(ResourceManager):
    def __init__(self, *args, **kwargs):
        ResourceManager.__init__(self, *args, **kwargs)
