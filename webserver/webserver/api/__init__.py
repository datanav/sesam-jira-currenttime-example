import collections
from flask import render_template, request, current_app
import pathlib

from .customfield_mappings.csv import get_customfield_mapping_results
from .compare_totals.csv import get_totals_searchresults
from .currenttime_with_jira_keys.csv import get_current_time_with_jira_keys_results
from .utils import get_search_results_by_query, assert_user_name_from_request

def get_administered_currenttime_subtasks():
    # NOTE: the CurrentTime web gui labels the task and subtask as 'Subproject' and 'Task', so that is what we ",
    # need to do here, since this will be displayed to the end-user.",
    #  project => 'Project'",
    #  task => 'Subproject'",
    #  subtask => 'Task'"


    user_name = assert_user_name_from_request()

    administered_subtasks = get_search_results_by_query(
        doctype="currenttime-subtask",
        query={
            "filtered": {
                "filter": {
                    "bool": {
                        "should": [
                            {
                                "term": {"subtask_attesting_user_name": user_name}
                            },
                            {
                                "term": {"subtask_leader_user_name": user_name}
                            }
                        ],
                    }
                }
            }
        })

    administered_subtasks.sort(key=lambda subtask: (subtask["projectname"], subtask["taskname"], subtask["subtaskname"]))
    return administered_subtasks

def get():
    swagger_file_url = pathlib.PurePosixPath("/", current_app.config["virtualhost_path"],
                                             "swagger.json").as_posix()

    totals_results = get_totals_searchresults()[1]
    current_time_with_jira_keys_results = get_current_time_with_jira_keys_results()[1]
    customfield_mapping_results = get_customfield_mapping_results()[1]

    administered_currenttime_subtasks  = get_administered_currenttime_subtasks()


    return render_template("frontpage.html",
                           swagger_file_url=swagger_file_url,
                           totals_results=totals_results,
                           current_time_with_jira_keys_results=current_time_with_jira_keys_results,
                           customfield_mapping_results=customfield_mapping_results,
                           administered_currenttime_subtasks=administered_currenttime_subtasks,
                           user_name = assert_user_name_from_request()
                           )
