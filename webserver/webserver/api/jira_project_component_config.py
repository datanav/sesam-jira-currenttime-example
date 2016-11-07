import json
import threading
import time

import flask
import sesamclient
from flask import request

from .customfieldvalue_config import get_ct_project_task_subtask
from .utils import assert_user_name_from_request


_cached_jira_projects = None
_cached_jira_projects_lock = threading.RLock()


def lowercase_name_sort_key(item):
    "utility-function used with list.sort"
    return item["name"].lower()

def get_jira_projects():
    global _cached_jira_projects
    with _cached_jira_projects_lock:
        if _cached_jira_projects is not None:
            age = time.monotonic() - _cached_jira_projects["timestamp"]
            if age < 3600:
                return _cached_jira_projects["value"]

        sesam_url = flask.current_app.config["sesam_base_url"]

        with sesamclient.Connection(sesam_url) as connection:
            #########################################################################################
            # Get the JIRA projects and components
            #########################################################################################
            project_dataset = connection.get_dataset("jira-project")

            formatted_projects = {}
            for project in project_dataset.get_entities(history=False, deleted=False):
                formatted_projects[project["ID"]] = {
                    "name": "%s (%s-*)" % (project["pname"], project["pkey"]),
                    "id": int(project["ID"]),
                    "components": []
                }


            component_dataset = connection.get_dataset("jira-component")

            # connect components to projects
            for component in component_dataset.get_entities(history=False, deleted=False):
                project_id = component["PROJECT"]
                # it is possible, though unlikely that we get a component with no matching project. It can happen
                # if a new JIRA project and its components has recently been added, and we have only read the new
                # entries from the components-table so far.
                if project_id in formatted_projects:
                    formatted_project = formatted_projects[project_id]
                    formatted_project["components"].append({
                        "name": component["cname"],
                        "id": int(component["ID"]),
                    })

            # format the information for the clientside javascript
            formatted_projects = list(formatted_projects.values())
            formatted_projects.sort(key=lowercase_name_sort_key)
            formatted_projects.insert(0, {
                "name": "*Select a project*",
                "id": "0",
                "components": []
            })

            for formatted_project in formatted_projects:
                components = formatted_project["components"]
                if len(components) > 0:
                    components.sort(key=lowercase_name_sort_key)
                    components.insert(0, {
                        "name": "*All*",
                        "id": 0
                    })
            jira_projects_as_json = json.dumps(formatted_projects)
            _cached_jira_projects = {"timestamp": time.monotonic(),
                                                "value": jira_projects_as_json,
                                                "raw_value": formatted_projects,
                                                }
            return jira_projects_as_json


def get_mappings_html():
    sesam_url = flask.current_app.config["sesam_base_url"]
    with sesamclient.Connection(sesam_url) as connection:
        #########################################################################################
        # Get the JIRA project&component mappings
        #########################################################################################
        dataset = connection.get_dataset("cooked-config-jira-project-component-to-currenttime-subtask")
        if dataset is None:
            # the dataset is not yet created. This is normal.
            mapping_entities = []
        else:
            mapping_entities = list(dataset.get_entities(history=False, deleted=False))

        mapping_entities.sort(key=lambda x: (x["jira_project_name"] or "",
                                             x["jira_component_name"] or "",
                                             x["currenttime_projectname"] or "",
                                             x["currenttime_taskname"] or "",
                                             x["currenttime_subtaskname"] or "",
                                             ))
        return flask.render_template("jira_project_component_config_mappings.html",
                                     mappings=mapping_entities)




def get():
    jira_projects = get_jira_projects()
    currenttime_projects = get_ct_project_task_subtask()

    mappings = get_mappings_html()
    return flask.render_template("jira_project_component_config.html",
                                 jira_projects=jira_projects,
                                 currenttime_projects=currenttime_projects,
                                 mappings=mappings
                           )


def post():
    user_name = assert_user_name_from_request()
    delete_mapping = request.form.get("delete") == "1"
    if delete_mapping:
        # The user wants to delete an existing mapping
        mapping_id = request.form.get("mapping_id")
        if not mapping_id:
            return "<p>No mapping_id was specified!</p>" + get_mappings_html()
        entity = {"_id": mapping_id,
                  "_deleted": True,
                  "deleted_by": user_name}
    else:
        # The user wants to add a new mapping or update an existing one
        jira_project_id = int(request.form.get("jira-project", "0"))
        jira_component_id = int(request.form.get("jira-component", "0"))

        ct_project_id = int(request.form.get("currenttime-project", "0"))
        ct_task_id = int(request.form.get("currenttime-task", "0"))
        ct_subtask_id = int(request.form.get("currenttime-subtask", "0"))

        if not jira_project_id:
            return "<p>A JIRA Project must be selected!</p>" + get_mappings_html()

        if not (ct_project_id and ct_task_id and ct_subtask_id):
            return "<p>A CurrentTime project, task and subtask must be selected!</p>" + get_mappings_html()

        entity = {
            "_id": "%d_%d" % (jira_project_id, jira_component_id),
            "jira_project_id": jira_project_id,
            "jira_component_id": jira_component_id,
            "currenttime_project_id": ct_project_id,
            "currenttime_task_id": ct_task_id,
            "currenttime_subtask_id": ct_subtask_id,
            "added_by": user_name}

    sesam_url = flask.current_app.config["sesam_base_url"]
    with sesamclient.Connection(sesam_url) as connection:
        #########################################################################################
        # Get the JIRA customfield mappings
        #########################################################################################
        mapping_pipe = connection.get_pipe("config-jira-project-component-to-currenttime-subtask")
        mapping_pipe.post_entities([entity])

        # make sure the cooked version (the one that has subtaskname, etc) is updated, since that is the one we use
        # in get_mappings_html().
        cooked_mapping_pump = connection.get_pipe("cooked-config-jira-project-component-to-currenttime-subtask").get_pump()
        cooked_mapping_pump.wait_for_pump_to_finish_running()
        cooked_mapping_pump.start()
        cooked_mapping_pump.wait_for_pump_to_finish_running()

    return get_mappings_html()

