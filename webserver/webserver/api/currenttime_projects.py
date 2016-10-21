from .utils import get_search_results_by_query


def get():
    projects = get_search_results_by_query(doctype="currenttime-project",
                                           query={"bool": {
                                               "filter": [
                                                   {"term": {"projectactive": 1}},
                                                   {"term": {"is_internal_projecttype": False}}
                                               ]
                                           }})
    results = []
    for project in projects:
        results.append({
            "id": project["projectid"],
            "name": project["projectname"],
        })
    return results
