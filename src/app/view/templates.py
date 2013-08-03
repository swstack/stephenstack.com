import jinja2


class TemplateBuilder(object):
    def __init__(self, resource_manager):
        self._resource_manager = resource_manager
        self._jinja_env = None

    def start(self):
        self._jinja_env = \
            jinja2.Environment(
                loader=jinja2.FileSystemLoader(
                        self._resource_manager.get_fs_resource_path("templates")),
                autoescape=True)

    def get_index(self, template_vars):
        index = self._jinja_env.get_template("index.html")
        return index.render(template_vars)

    def get_admin(self, template_vars):
        index = self._jinja_env.get_template("admin.html")
        return index.render(template_vars)
