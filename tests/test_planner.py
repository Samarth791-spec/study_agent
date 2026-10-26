import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
from _planner import PlanError, handle_request, make_plan  # noqa: E402

BASE = {
    "start_date": "2026-11-01", "hours_per_day": 4, "rest_day": 6,
    "subjects": [
        {"name": "Maths", "exam_date": "2026-11-15", "difficulty": 5, "confidence": 2},
        {"name": "History", "exam_date": "2026-11-10", "difficulty": 2, "confidence": 4},
    ],
}


def test_every_study_day_uses_all_hours():
    plan = make_plan(BASE)
    for day in plan["days"]:
        if day["blocks"]:
            assert sum(b["minutes"] for b in day["blocks"]) == 240


def test_hard_low_confidence_subject_gets_more_time():
    hours = {s["subject"]: s["planned_hours"] for s in make_plan(BASE)["summary"]}
    assert hours["Maths"] > hours["History"]


def test_rest_day_is_empty():
    plan = make_plan(BASE)
    sundays = [d for d in plan["days"] if d["weekday"] == "Sunday" and not d["exams"]]
    assert sundays and all(d["rest"] and not d["blocks"] for d in sundays)


def test_no_study_after_exam():
    plan = make_plan(BASE)
    for day in plan["days"]:
        if day["date"] > "2026-11-10":
            assert all(b["subject"] != "History" for b in day["blocks"])


def test_day_before_exam_is_final_revision():
    plan = make_plan(BASE)
    day = next(d for d in plan["days"] if d["date"] == "2026-11-14")
    assert all(b["mode"] == "Final revision" for b in day["blocks"])


def test_bad_input():
    assert handle_request(b"not json")[0] == 400
    bad = dict(BASE, subjects=[])
    assert handle_request(__import__("json").dumps(bad).encode())[0] == 400
    try:
        make_plan(dict(BASE, subjects=[{"name": "X", "exam_date": "2020-01-01"}]))
    except PlanError:
        return
    assert False


def test_tight_schedule_warns():
    tight = dict(BASE, hours_per_day=0.5)
    assert any("Time is tight" in a for a in make_plan(tight)["advice"])
