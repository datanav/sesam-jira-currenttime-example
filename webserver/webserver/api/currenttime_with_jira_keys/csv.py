import collections

from .. import utils


def get_current_time_with_jira_keys_results():
    # NOTE: the CurrentTime web gui labels the task and subtask as 'Subproject' and 'Task', so that is what we ",
    # need to do here, since this will be displayed to the end-user.",
    #  project => 'Project'",
    #  task => 'Subproject'",
    #  subtask => 'Task'"
    fieldmapping = collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("CT hours", "timeworked"),
                               ("JIRA hours", "total_jira_timeworked"),
                               ("CT Project", "ct_projectname"),
                               ("CT Subproject", "ct_taskname"),
                               ("CT Task", "ct_subtaskname"),
                               ("JIRA keys", "jira_issue_keys")])
    return fieldmapping, utils.get_search_results(doctype="workentry-currenttime-with-jira-keys",
                                    fieldmapping=fieldmapping)

def get():
    fieldmapping, results = get_current_time_with_jira_keys_results()
    return utils.serve_csv_file(results, filename="currenttime-with-jira-keys.csv", fieldmapping=fieldmapping)
