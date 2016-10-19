import collections

from . import utils


def get():
    return utils.serve_csv_file(doctype="workentry-currenttime-with-jira-keys",
                           filename="currenttime-with-jira-keys.csv",
                           fieldmapping=collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("CT hours", "timeworked"),
                               ("JIRA hours", "total_jira_timeworked"),
                               ("CT subtask", "ct_subtaskname"),
                               ("CT task", "ct_taskname"),
                               ("CT project", "ct_projectname"),
                               ("CT projecttype", "ct_projecttypename"),
                               ("JIRA keys", "jira_issue_keys")]))
