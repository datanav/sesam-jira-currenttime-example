from .utils import get_search_results_by_query


def get(task_id):
    subtasks = get_search_results_by_query(doctype="currenttime-subtask",
                                           query={"match": {"taskid": task_id}})
    results = []
    for subtask in subtasks:
        results.append({
            "id": subtask["subtaskid"],
            "name": subtask["subtaskname"],
        })
    return results
