import collections

from .. import utils


def get_jira_project_component_mapping_results():
    # NOTE: the CurrentTime web gui labels the task and subtask as 'Subproject' and 'Task', so that is what we ",
    # need to do here, since this will be displayed to the end-user.",
    #  project => 'Project'",
    #  task => 'Subproject'",
    #  subtask => 'Task'"
    fieldmapping = collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("CT hours", "timeworked_from_currenttime"),
                               ("JIRA hours", "timeworked_from_jira"),
                               ("CT Project", "ct_projectname"),
                               ("CT Subproject", "ct_taskname"),
                               ("CT Task", "ct_subtaskname"),
                               ("JIRA issues", "jira_issue_key_hours")])
    return fieldmapping, utils.get_search_results(doctype="project-component-mapping",
                                    fieldmapping=fieldmapping)

def get():
    fieldmapping, results = get_jira_project_component_mapping_results()
    return utils.serve_csv_file(results, filename="jira-project-component-mappings.csv", fieldmapping=fieldmapping)
