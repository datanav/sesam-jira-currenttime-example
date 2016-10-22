import collections

from .. import utils


def get_customfield_mapping_results():
    fieldmapping = collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("CT hours", "timeworked_from_currenttime"),
                               ("JIRA hours", "timeworked_from_jira"),
                               ("CT subtask", "ct_subtaskname"),
                               ("CT task", "ct_taskname"),
                               ("CT project", "ct_projectname"),
                               ("CT projecttype", "ct_projecttypename"),
                               ("JIRA issues", "jira_issue_key_hours")])
    return fieldmapping, utils.get_search_results(doctype="customfield-mapping",
                                    fieldmapping=fieldmapping)

def get():
    fieldmapping, results = get_customfield_mapping_results()
    return utils.serve_csv_file(results, filename="customfield-mappings.csv", fieldmapping=fieldmapping)
