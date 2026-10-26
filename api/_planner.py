"""The agent brain. Pure Python, standard library only: no API, no keys.

Idea: every half hour of study time is given to the subject that
needs it most right now. "Need" grows when a subject is hard, when
your confidence is low, and when its exam is getting close.
"""
import json
from datetime import date, timedelta

BLOCK_MIN = 30          # one study block = 30 minutes
MAX_SUBJECTS = 12
MAX_DAYS = 120

TIPS = {
    "Learn": "Read the topic, write short notes, then try 5 practice questions.",
    "Revise": "Solve practice problems or past papers. Mark what you get wrong.",
    "Final revision": "Skim notes, formulas and weak points only. Sleep early.",
}


class PlanError(ValueError):
    """Bad input from the user. Shown as a friendly message."""


def clamp(value, low, high):
    return max(low, min(high, value))


def read_subjects(raw, start):
    if not isinstance(raw, list) or not raw:
        raise PlanError("Add at least one subject.")
    if len(raw) > MAX_SUBJECTS:
        raise PlanError(f"Please use {MAX_SUBJECTS} subjects or fewer.")
    subjects = []
    for i, item in enumerate(raw):
        name = str(item.get("name", "")).strip()[:40]
        if not name:
            raise PlanError(f"Subject {i + 1} needs a name.")
        try:
            exam = date.fromisoformat(str(item.get("exam_date", "")))
        except ValueError:
            raise PlanError(f"'{name}' needs a valid exam date.")
        if exam <= start:
            raise PlanError(f"'{name}': exam date must be after the start date.")
        if (exam - start).days > MAX_DAYS:
            raise PlanError(f"'{name}': exam is more than {MAX_DAYS} days away.")
        difficulty = clamp(int(item.get("difficulty", 3)), 1, 5)
        confidence = clamp(int(item.get("confidence", 3)), 1, 5)
        need = difficulty * (6 - confidence)          # 1 .. 25
        subjects.append({"id": i, "name": name, "exam": exam,
                         "difficulty": difficulty, "confidence": confidence,
                         "need": need})
    return subjects


def mode_for(days_left):
    if days_left <= 1:
        return "Final revision"
    if days_left <= 3:
        return "Revise"
    return "Learn"


def pick_subject(active, today, done_blocks):
    """The heart of the agent: who needs the next block most?"""
    def score(s):
        days_left = (s["exam"] - today).days
        urgency = 1 + 6 / days_left                    # 1.05 far away .. 7 tomorrow
        return s["need"] * urgency / (1 + done_blocks[s["id"]])
    return max(active, key=score)


def make_plan(data):
    try:
        start = date.fromisoformat(data["start_date"]) if data.get("start_date") else date.today()
        hours = clamp(float(data.get("hours_per_day", 3)), 0.5, 12)
    except (ValueError, TypeError):
        raise PlanError("Check the start date and daily hours.")
    rest = data.get("rest_day")
    rest = int(rest) if rest not in (None, "", "none") else None

    subjects = read_subjects(data.get("subjects"), start)
    last_exam = max(s["exam"] for s in subjects)
    blocks_per_day = int(hours * 2)
    done = {s["id"]: 0 for s in subjects}

    days, day = [], start
    while day <= last_exam:
        entry = {"date": day.isoformat(), "weekday": day.strftime("%A"),
                 "exams": [s["name"] for s in subjects if s["exam"] == day],
                 "rest": False, "blocks": []}
        active = [s for s in subjects if s["exam"] > day]
        is_rest = rest is not None and day.weekday() == rest
        if is_rest and not entry["exams"]:
            entry["rest"] = True
        elif active:
            todays = {}
            for _ in range(blocks_per_day):
                chosen = pick_subject(active, day, done)
                done[chosen["id"]] += 1
                todays[chosen["id"]] = todays.get(chosen["id"], 0) + 1
            by_id = {s["id"]: s for s in subjects}
            order = sorted(todays, key=lambda sid: (by_id[sid]["exam"], sid))
            for sid in order:
                s = by_id[sid]
                mode = mode_for((s["exam"] - day).days)
                entry["blocks"].append({
                    "subject": s["name"], "subject_id": sid,
                    "minutes": todays[sid] * BLOCK_MIN,
                    "mode": mode, "tip": TIPS[mode],
                    "exam_in_days": (s["exam"] - day).days,
                })
        days.append(entry)
        day += timedelta(days=1)

    summary, shortfall = [], 0.0
    for s in subjects:
        planned = done[s["id"]] * BLOCK_MIN / 60
        wanted = max(2.0, float(s["need"]))
        enough = planned >= wanted * 0.8
        shortfall += 0 if enough else wanted - planned
        summary.append({"subject": s["name"], "subject_id": s["id"],
                        "exam": s["exam"].isoformat(),
                        "difficulty": s["difficulty"], "confidence": s["confidence"],
                        "planned_hours": round(planned, 1),
                        "recommended_hours": round(wanted, 1), "enough": enough})

    study_days = max(1, sum(1 for d in days if d["blocks"]))
    advice = ["Take a 5-minute break after every 50 minutes of study."]
    if shortfall > 0:
        extra = round(shortfall / study_days, 1)
        advice.insert(0, f"Time is tight. Add about {extra} more hour(s) per day, "
                         "or move a rest day to study time.")
    weak = [s["name"] for s in subjects if s["confidence"] <= 2]
    if weak:
        advice.append("Low confidence in: " + ", ".join(weak) + ". Start these first each day.")
    return {"start_date": start.isoformat(), "hours_per_day": hours,
            "days": days, "summary": summary, "advice": advice}


def handle_request(body_bytes):
    """Shared by the Vercel function and the local server. Returns (status, dict)."""
    try:
        data = json.loads(body_bytes or b"{}")
        return 200, make_plan(data)
    except PlanError as error:
        return 400, {"error": str(error)}
    except (ValueError, TypeError, AttributeError):
        return 400, {"error": "Invalid input. Please check the form."}
