import connexion
import connexion.app
import elasticsearch
from flask import g
import sys


from connexion.resolver import RestyResolver
import yaml
import os.path

def main():
    app = connexion.App(__name__)
    flaskapp = app.app

    if len(sys.argv) > 1:
        configfilename = sys.argv[1]
    else:
        configfilename = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(configfilename) as configfile:
        flaskapp.config.update(yaml.safe_load(configfile))

    app.add_api(os.path.join(os.path.dirname(__file__), 'swagger.yaml'), resolver=RestyResolver('api'))

    @flaskapp.after_request
    def add_header(response):
        response.cache_control.max_age = 0
        response.cache_control.no_cache = True
        return response

    app.run(port=8080)


if __name__ == "__main__":
    main()