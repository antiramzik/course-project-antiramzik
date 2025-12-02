import json

from app.utils.problem import problem


def test_problem_shape_fields():
    resp = problem(404, "Not Found", "resource missing")
    data = json.loads(resp.body.decode("utf-8"))
    assert data["type"] == "about:blank"
    assert data["title"] == "Not Found"
    assert data["status"] == 404
    assert data["detail"] == "resource missing"
    assert isinstance(data.get("correlation_id"), str) and len(data["correlation_id"]) > 5


def test_problem_unique_correlation_id():
    a = problem(400, "Bad Request", "a")
    b = problem(400, "Bad Request", "b")
    da = json.loads(a.body.decode("utf-8"))
    db = json.loads(b.body.decode("utf-8"))
    assert da["correlation_id"] != db["correlation_id"]
