import copy
import logging
import pkg_resources
import os.path
import sys
import urllib.parse
import connexion
import connexion.app
import flask
import yaml
from connexion.resolver import RestyResolver
import werkzeug.contrib.fixers

logging.basicConfig(level=logging.INFO)


class MySwaggerResolver(connexion.Resolver):
    """
    Resolves endpoint functions based on the endpoint path and method
    """

    def __init__(self, default_module_name):
        """
        :param default_module_name: Default module name for operations
        :type default_module_name: str
        """
        connexion.Resolver.__init__(self)
        self.default_module_name = default_module_name

    def resolve_operation_id(self, operation):
        """
        Resolves the operationId based on the endpoint path and method unless explicitly configured in the spec

        :type operation: connexion.operation.Operation
        """
        if operation.operation.get('operationId'):
            return super().resolve_operation_id(operation)

        operation_path_elements = []
        for element in operation.path.lstrip("/").rstrip("/").split("/"):
            if element.startswith("{"):
                # this is a dynamic parameter, so we stop the routing here
                break
            operation_path_elements.append(element)

        def get_controller_name():
            x_router_controller = operation.operation.get('x-swagger-router-controller')

            name = self.default_module_name
            resource_name = ".".join(operation_path_elements)

            if x_router_controller:
                name = x_router_controller

            elif resource_name:
                resource_controller_name = resource_name.replace('-', '_')
                name += '.' + resource_controller_name

            return name

        def get_function_name():
            return operation.method.lower()

        return '{}.{}'.format(get_controller_name(), get_function_name())


def main():
    if len(sys.argv) > 1:
        configfilename = sys.argv[1]
    else:
        configfilename = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(configfilename) as configfile:
        config = yaml.safe_load(configfile)

    app = connexion.App(__name__)
    flaskapp = app.app

    flaskapp.config.update(config)

    flaskapp.wsgi_app = werkzeug.contrib.fixers.ProxyFix(flaskapp.wsgi_app)

    public_api = app.add_api(
        pkg_resources.resource_filename(__name__, 'swagger.yaml'),
        resolver=MySwaggerResolver('api'),
        swagger_json=False  # We need to return a customized swagger.conf in order to handle VirtualHost'ing
        )

    @flaskapp.after_request
    def add_header(response):
        response.expires = None
        response.cache_control.max_age = 0
        response.cache_control.no_cache = True
        response.cache_control.private = True
        response.cache_control.public = False
        return response

    @app.route("/swagger.json")
    def swagger_json():
        """Since the webserver is hidden behind a Apache VirtualHost (or similar), we must tweak the

        """
        specification = copy.deepcopy(public_api.specification)
        # Add the correct basePath. This must be set dynamically, since this webserver might be served
        # from behind an Apache VirtualHost.
        request = flask.request
        specification["basePath"] = "/" + urllib.parse.urljoin(flaskapp.config["virtualhost_path"],
                                                               request.script_root)

        return flask.jsonify(specification)

    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
