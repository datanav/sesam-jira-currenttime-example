
from flask import render_template, request, current_app
import pathlib


def get():
    swagger_file_url = pathlib.PurePosixPath("/", current_app.config["virtualhost_path"],
                                             "swagger.json").as_posix()
    return render_template("frontpage.html", swagger_file_url=swagger_file_url)
