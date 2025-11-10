# pricing.py
import json
import math
from datetime import date, timedelta

def load_spec(text: str, fallback: dict) -> tuple[dict, str | None]:
    try:
        return json.loads(text), None
    except Exception as e:
        return fallback, f"JSON parse error: {e}"

def currency(spec: dict) -> str:
    return spec.get("currency", "USD")

def timeline_policy(spec: dict) -> dict:
    return spec.get("timeline_policy", {})

def working_days_per_week(spec: dict) -> int:
    return int(timeline_policy(spec).get("working_days_per_week", 5))

def parallel_sources(spec: dict) -> int:
    return max(1, int(timeline_policy(spec).get("parallel_sources", 1)))

def buffer_days(spec: dict) -> int:
    return int(timeline_policy(spec).get("buffer_days", 0))

def to_calendar_days(business_days: int, wd_per_week: int) -> int:
    return math.ceil(business_days * 7 / max(1, wd_per_week))

def add_business_days(start: date, business_days: int, wd_per_week: int) -> date:
    if wd_per_week == 5:
        days_added = 0
        current = start
        while days_added < business_days:
            current += timedelta(days=1)
            if current.weekday() < 5:
                days_added += 1
        return current
    else:
        cal = to_calendar_days(business_days, wd_per_week)
        return start + timedelta(days=cal)

def compute_layer1_time(impl_days_sum: int, par: int) -> int:
    return math.ceil(impl_days_sum / max(1, par))
