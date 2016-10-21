from .utils import get_search_results_by_query


def get(project_id):
    tasks = get_search_results_by_query(doctype="currenttime-task",
                                        query={"match": {"projectid": project_id}})
    results = []
    for task in tasks:
        results.append({
            "id": task["taskid"],
            "name": task["taskname"],
        })
    return results
