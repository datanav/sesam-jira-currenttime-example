import json
import operator

import collections
import pprint
import threading

import flask
import sesamclient
import time

from flask import request

from .utils import get_search_results_by_query


_cached_jira_customfields = None
_cached_jira_customfields_lock = threading.RLock()


def get_jira_customfields():
    global _cached_jira_customfields
    with _cached_jira_customfields_lock:
        if _cached_jira_customfields is not None:
            age = time.monotonic() - _cached_jira_customfields["timestamp"]
            if age < 3600:
                return _cached_jira_customfields["value"]

        sesam_url = flask.current_app.config["sesam_base_url"]

        with sesamclient.Connection(sesam_url) as connection:
            #########################################################################################
            # Get the JIRA customfield options
            #########################################################################################
            customfield_dataset = connection.get_dataset("jira-customfield")
            customfield_list = list(customfield_dataset.get_entities(history=False, deleted=False))

            customfields = {}
            for customfield in customfield_list:
                customfields[customfield["ID"]] = customfield

            customfieldoption_dataset = connection.get_dataset("jira-customfieldoption")
            customfieldoptions_list = list(customfieldoption_dataset.get_entities(history=False, deleted=False))
            customfieldoptions_list.sort(key=operator.itemgetter("SEQUENCE"))

            customfieldoptions = {}
            for customfieldoption in customfieldoptions_list:
                customfieldoptions[customfieldoption["ID"]] = {"option": customfieldoption,
                                                                     "child_options": []}

            # connect children to parents
            for customfieldoption in customfieldoptions_list:
                parent_id = customfieldoption["PARENTOPTIONID"]
                if parent_id:
                    parent_option = customfieldoptions[parent_id]
                    if parent_option["option"]["CUSTOMFIELD"] != customfieldoption["CUSTOMFIELD"]:
                        return ("""ERROR: parent_option["CUSTOMFIELD"](%s) != customfieldoption["CUSTOMFIELD"](%s)!
        parent_option:\n%s\n\n\n
        customfieldoption:\n%s\n
                        """ % (
                            parent_option["CUSTOMFIELD"], customfieldoption["CUSTOMFIELD"],
                            pprint.pformat(parent_option), pprint.pformat(customfieldoption)
                        ))
                    parent_option["child_options"].append(customfieldoption)

                    if parent_option["option"]["PARENTOPTIONID"]:
                        return ("""ERROR: parent_option["PARENTOPTIONID"](%s) is not null! This means that there are more than two layers of customoptionvalues! This is not supported!
        parent_option:\n%s\n\n\n
        customfieldoption:\n%s\n
                        """ % (
                            parent_option["PARENTOPTIONID"],
                            pprint.pformat(parent_option), pprint.pformat(customfieldoption)
                        ))

            # find root options for each customfield
            customfield_id_to_rootoptions = collections.defaultdict(list)
            for option_id, option_info in customfieldoptions.items():
                if not option_info["option"]["PARENTOPTIONID"]:
                    customfield_id_to_rootoptions[option_info["option"]["CUSTOMFIELD"]].append(option_info)


            # format the information with for the clientside javascript
            jira_customfields = []
            for customfield_id, root_options in customfield_id_to_rootoptions.items():
                customfield = customfields[customfield_id]
                formatted_root_options = [{
                            "name": "*Select a value*",
                            "id": "0",
                        }]
                for root_option in root_options:
                    children = []
                    for child in root_option["child_options"]:
                        children.append({
                            "name": child["customvalue"],
                            "id": str(int(child["ID"])),
                        })
                    root_option_info = root_option["option"]
                    formatted_root_option = {
                      "name": root_option_info["customvalue"],
                      "id": str(int(root_option_info["ID"])),
                    }
                    if children:
                        children.insert(0, {
                            "name": "*All*",
                            "id": "0",
                        })
                        formatted_root_option["suboptions"] = children

                    formatted_root_options.append(formatted_root_option)
                jira_customfields.append(
                    {
                        "name": customfield["cfname"],
                        "description": customfield["DESCRIPTION"],
                        "id": int(customfield["ID"]),
                        "options": formatted_root_options
                    }
                )

            jira_customfields.sort(key=operator.itemgetter("name"))
            jira_customfields_as_json = json.dumps(jira_customfields)
            _cached_jira_customfields = {"timestamp": time.monotonic(),
                                                "value": jira_customfields_as_json,
                                                "raw_value": jira_customfields,
                                                }
            return jira_customfields_as_json


_cached_ct_project_task_subtask = None
_cached_ct_project_task_subtask_lock = threading.RLock()


def get_ct_project_task_subtask():
    global _cached_ct_project_task_subtask
    with _cached_ct_project_task_subtask_lock:
        if _cached_ct_project_task_subtask is not None:
            age = time.monotonic() - _cached_ct_project_task_subtask["timestamp"]
            if age < 3600:
                return _cached_ct_project_task_subtask["value"]


        ###########################################################################33
        # Get the CurrentTime project=>task=>subtask hierarcy
        ###########################################################################33
        ct_subtasks = get_search_results_by_query(
            doctype="currenttime-subtask",
            # We use source-filtering to cut down the size of the returned doc. This speeds things up.
            _source=["projectid", "projectname", "taskid", "taskname", "subtaskid", "subtaskname"],
            query={"bool": {
                "filter": [
                    {"term": {"projectactive": 1}},
                    {"term": {"is_internal_projecttype": False}}
                ]
            }},
            sort=[
                {"projectname": {"order": "asc"}},
                {"taskname": {"order": "asc"}},
                {"subtaskname": {"order": "asc"}},
            ])
        ct_projects = collections.OrderedDict()
        for ct_subtask in ct_subtasks:
            project_id = str(ct_subtask["projectid"])
            task_id = str(ct_subtask["taskid"])
            subtask_id = ct_subtask["subtaskid"]
            try:
                project = ct_projects[project_id]
            except KeyError:
                project = ct_projects[project_id] = {
                    "id": project_id,
                    "name": ct_subtask["projectname"],
                    "tasks": collections.OrderedDict()
                }
                project["tasks"][0] = {
                    "id": 0,
                    "name": "*Select a Task*",
                    "subtasks": {}
                }
            try:
                task = project["tasks"][task_id]
            except KeyError:
                task = project["tasks"][task_id] = {
                    "id": task_id,
                    "name": ct_subtask["taskname"],
                    "subtasks": collections.OrderedDict()
                }
                task["subtasks"][0] = {
                    "id": 0,
                    "name": "*Select a Subtask*"
                }
            task["subtasks"][subtask_id] = {
                "id": subtask_id,
                "name": ct_subtask["subtaskname"]
            }

        # The elasticsearch "sort" stuff doesn't seem to work, so we have to do it here
        ct_projects = sorted(ct_projects.values(), key=operator.itemgetter("name"))

        for project in ct_projects:
            project["tasks"] = sorted(project["tasks"].values(), key=operator.itemgetter("name"))
            for task in project["tasks"]:
                task["subtasks"] = sorted(task["subtasks"].values(), key=operator.itemgetter("name"))

        ct_projects_as_json = json.dumps(ct_projects)
        _cached_ct_project_task_subtask = {"timestamp": time.monotonic(),
                                           "value": ct_projects_as_json,
                                           "raw_value": ct_projects}
        return ct_projects_as_json


def get_mappings_html():
    sesam_url = flask.current_app.config["sesam_base_url"]
    with sesamclient.Connection(sesam_url) as connection:
        #########################################################################################
        # Get the JIRA customfield mappings
        #########################################################################################
        dataset = connection.get_dataset("cooked-config-jira-customfieldvalue-to-currenttime-subtask")
        if dataset is None:
            # the dataset is not yet created. This is normal.
            mapping_entities = []
        else:
            mapping_entities = list(dataset.get_entities(history=False, deleted=False))

        mapping_entities.sort(key=lambda x: (x["jira_customfield_name"] or "",
                                             x["jira_customfield_option_value"] or "",
                                             x["jira_customfield_suboption_value"] or "",
                                             x["currenttime_projectname"] or "",
                                             x["currenttime_taskname"] or "",
                                             x["currenttime_subtaskname"] or "",
                                             ))
        return flask.render_template("customfieldvalue_config_mappings.html",
                                     mappings=mapping_entities)




def get():
    jira_customfields = get_jira_customfields()
    currenttime_projects = get_ct_project_task_subtask()

    mappings = get_mappings_html()
    return flask.render_template("customfieldvalue_config.html",
                                 jira_customfields=jira_customfields,
                                 currenttime_projects=currenttime_projects,
                                 mappings=mappings
                           )


def post():
    delete_mapping = request.form.get("delete") == "1"
    if delete_mapping:
        # The user wants to delete an existing mapping
        mapping_id = request.form.get("mapping_id")
        if not mapping_id:
            return "<p>No mapping_id was specified!</p>" + get_mappings_html()
        entity = {"_id": mapping_id, "_deleted": True}
    else:
        # The user wants to add a new mapping or update an existing one
        jira_customfield_id = int(request.form.get("jira-customfield", "0"))
        jira_customfield_option_id = int(request.form.get("jira-customfield-option", "0"))
        jira_customfield_suboption_id = int(request.form.get("jira-customfield-suboption", "0"))

        ct_project_id = int(request.form.get("currenttime-project", "0"))
        ct_task_id = int(request.form.get("currenttime-task", "0"))
        ct_subtask_id = int(request.form.get("currenttime-subtask", "0"))


        if not (jira_customfield_id and jira_customfield_option_id):
            return "<p>A JIRA customfield and customfield value must be selected!</p>" + get_mappings_html()

        if not (ct_project_id and ct_task_id and ct_subtask_id):
            return "<p>A CurrentTime project, task and subtask must be selected!</p>" + get_mappings_html()

        entity = {
            "_id": "%d_%d_%d" % (jira_customfield_id, jira_customfield_option_id, jira_customfield_suboption_id),
            "jira_customfield_id": jira_customfield_id,
            "jira_customfield_option_id": jira_customfield_option_id,
            "jira_customfield_suboption_id": jira_customfield_suboption_id,
            "currenttime_project_id": ct_project_id,
            "currenttime_task_id": ct_task_id,
            "currenttime_subtask_id": ct_subtask_id}

    sesam_url = flask.current_app.config["sesam_base_url"]
    with sesamclient.Connection(sesam_url) as connection:
        #########################################################################################
        # Get the JIRA customfield mappings
        #########################################################################################
        mapping_pipe = connection.get_pipe("config-jira-customfieldvalue-to-currenttime-subtask")
        mapping_pipe.post_entities([entity])

        # make sure the cooked version (the one that has subtaskname, etc) is updated, since that is the one we use
        # in get_mappings_html().
        cooked_mapping_pump = connection.get_pipe("cooked-config-jira-customfieldvalue-to-currenttime-subtask").get_pump()
        cooked_mapping_pump.wait_for_pump_to_finish_running()
        cooked_mapping_pump.start()
        cooked_mapping_pump.wait_for_pump_to_finish_running()

    #return "jira_customfield_id:'%s', jira_customfield_option_id:'%s', jira_customfield_suboption_id:'%s', ct_project_id:'%s', ct_task_id:'%s', ct_subtask_id:'%s'" % (
    #    jira_customfield_id, jira_customfield_option_id, jira_customfield_suboption_id, ct_project_id, ct_task_id, ct_subtask_id
    #)

    return get_mappings_html()

