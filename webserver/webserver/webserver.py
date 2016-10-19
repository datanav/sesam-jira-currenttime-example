import copy
import logging
import os.path
import sys
import urllib.parse
import connexion
import connexion.app
import flask
import yaml
from connexion.resolver import RestyResolver
import werkzeug.contrib.fixers

logging.basicConfig(level=logging.DEBUG)


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
        os.path.join(os.path.dirname(__file__), 'swagger.yaml'),
        resolver=RestyResolver('api'),
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
