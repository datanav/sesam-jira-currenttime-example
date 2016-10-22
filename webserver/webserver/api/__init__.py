
from flask import render_template, request, current_app
import pathlib

from .customfield_mappings.csv import get_customfield_mapping_results
from .compare_totals.csv import get_totals_searchresults
from .currenttime_with_jira_keys.csv import get_current_time_with_jira_keys_results

def get():
    swagger_file_url = pathlib.PurePosixPath("/", current_app.config["virtualhost_path"],
                                             "swagger.json").as_posix()

    totals_results = get_totals_searchresults()[1]
    current_time_with_jira_keys_results = get_current_time_with_jira_keys_results()[1]
    customfield_mapping_results = get_customfield_mapping_results()[1]

    return render_template("frontpage.html",
                           swagger_file_url=swagger_file_url,
                           totals_results=totals_results,
                           current_time_with_jira_keys_results=current_time_with_jira_keys_results,
                           customfield_mapping_results=customfield_mapping_results
                           )
