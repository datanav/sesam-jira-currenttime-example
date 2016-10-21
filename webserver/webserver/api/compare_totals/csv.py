import collections
from .. import utils


def get_totals_searchresults():
    fieldmapping = collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("JIRA hours", "total_timeworked_from_jira"),
                               ("CT hours", "total_timeworked_from_currenttime")])
    return fieldmapping, utils.get_search_results(doctype="compare-totals",
                           fieldmapping=fieldmapping)


def get():
    fieldmapping, results = get_totals_searchresults()
    return utils.serve_csv_file(results, filename="compare-totals.csv", fieldmapping=fieldmapping)
