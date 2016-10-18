import tempfile

import collections
from werkzeug.exceptions import InternalServerError

import elasticsearch
from flask import request, current_app, send_file

import os.path
import csv


def get_username_search_body():
    user_name = request.headers.get("x-remote-user")
    user_name = user_name.split("\\")[-1]  # remove any domainname from the user_name

    return {"query":
        {
            "bool": {
                "should": [
                    {
                        "term": {"user_name": user_name}
                    },
                    {
                        "term": {"ct_subtask_attesting_user_name": user_name}
                    },
                    {
                        "term": {"ct_subtask_leader_user_name": user_name}
                    }
                ],
            }
        }
    }


def _serve_csv_file(doctype, filename, fieldmapping):
    elasticsearch_client = elasticsearch.Elasticsearch(current_app.config["elasticsearch_host"])

    size = 10000
    search_result = elasticsearch_client.search(
        index="jira-currentime",
        doc_type=doctype,
        size=size,
        body=get_username_search_body())

    hits = search_result["hits"]
    if hits["total"] > size:
        raise InternalServerError(
            ("The total number of hits (%d) are larger than the maximum search page-size (%d)! "
             "TODO: implement search scrolling!") % (hits["total"], size))

    with tempfile.TemporaryDirectory() as tempdirname:
        csvfilename = os.path.join(tempdirname, filename)
        with open(csvfilename, "w", newline="", encoding="utf-8") as csvfile:
            cvswriter = csv.writer(csvfile, dialect='excel-tab')
            column_names = list(fieldmapping.keys())
            cvswriter.writerow(column_names)
            for hit in hits["hits"]:
                source_entity = hit["_source"]
                values = []
                for fieldname in fieldmapping.values():
                    value = source_entity[fieldname]
                    if isinstance(value, float):
                        # replace periods with commas in floating point numbers, since excel prefers that.
                        value = str(value).replace(".", ",")
                    values.append(value)

                cvswriter.writerow(values)

        return send_file(csvfilename)

def compare_totals():
    return _serve_csv_file(doctype="compare-totals",
                           filename="compare-totals.csv",
                           fieldmapping=collections.OrderedDict([
                               ("Date", "date"),
                               ("Username", "user_name"),
                               ("Errors", "errors"),
                               ("JIRA hours", "total_timeworked_from_jira"),
                               ("CT hours", "total_timeworked_from_currenttime")])
                           )


def currenttime_with_jira_keys():
    return _serve_csv_file(doctype="workentry-currenttime-with-jira-keys",
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
