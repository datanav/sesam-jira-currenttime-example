import csv
import os.path
import tempfile

import collections
import elasticsearch
import flask
from flask import request, current_app, send_file


def get_search_results_by_query(doctype, query, _source=True, size = 10000, sort=None):
    elasticsearch_client = elasticsearch.Elasticsearch(current_app.config["elasticsearch_host"])
    body = {"query": query}
    if sort:
        body["sort"] = sort
    search_result = elasticsearch_client.search(
        index="jira-currenttime",
        _source=_source,
        doc_type=doctype,
        size=size,
        body=body)

    results = []
    hits = search_result["hits"]
    for hit in hits["hits"]:
        source_entity = hit["_source"]
        results.append(source_entity)
    return results


def assert_user_name_from_request():
    user_name = request.headers.get("x-remote-user")
    if not user_name:
        flask.abort(401)
    user_name = user_name.split("\\")[-1]  # remove any domainname from the user_name
    return user_name


def get_search_results(doctype, fieldmapping):
    elasticsearch_client = elasticsearch.Elasticsearch(current_app.config["elasticsearch_host"])
    user_name = assert_user_name_from_request()

    size = 10000
    search_result = elasticsearch_client.search(
        index="jira-currenttime",
        doc_type=doctype,
        size=size,
        body={
            "query":
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
            },
            "sort": [
                {"date": {"order": "desc"}},
                {"user_name": {"order": "asc"}},
            ],
        })
    results = []
    hits = search_result["hits"]
    for hit in hits["hits"]:
        source_entity = hit["_source"]
        result = collections.OrderedDict()
        for uservisible_fieldnamename, fieldname in fieldmapping.items():
            value = source_entity[fieldname]
            if isinstance(value, float):
                # replace periods with commas in floating point numbers, since excel prefers that.
                value = str(value).replace(".", ",")
            result[uservisible_fieldnamename] = value
        results.append(result)
    return results


def serve_csv_file(results, filename, fieldmapping):
    with tempfile.TemporaryDirectory() as tempdirname:
        csvfilename = os.path.join(tempdirname, filename)
        with open(csvfilename, "w", newline="", encoding="utf-8") as csvfile:
            cvswriter = csv.writer(csvfile, dialect='excel-tab')
            column_names = list(fieldmapping.keys())
            cvswriter.writerow(column_names)
            for result in results:
                values = list(result.values())
                cvswriter.writerow(values)

        return send_file(csvfilename)
