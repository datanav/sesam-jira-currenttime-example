import collections

from .. import utils


def get_current_time_with_jira_keys_results():
    fieldmapping = collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("CT hours", "timeworked"),
                               ("JIRA hours", "total_jira_timeworked"),
                               ("CT subtask", "ct_subtaskname"),
                               ("CT task", "ct_taskname"),
                               ("CT project", "ct_projectname"),
                               ("CT projecttype", "ct_projecttypename"),
                               ("JIRA keys", "jira_issue_keys")])
    return fieldmapping, utils.get_search_results(doctype="workentry-currenttime-with-jira-keys",
                                    fieldmapping=fieldmapping)

def get():
    fieldmapping, results = get_current_time_with_jira_keys_results()
    return utils.serve_csv_file(results, filename="currenttime-with-jira-keys.csv", fieldmapping=fieldmapping)
