import collections
from . import utils


def get():
    return utils.serve_csv_file(doctype="compare-totals",
                           filename="compare-totals.csv",
                           fieldmapping=collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("JIRA hours", "total_timeworked_from_jira"),
                               ("CT hours", "total_timeworked_from_currenttime")])
                           )
