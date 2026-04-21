from __future__ import annotations


def evaluate_observation_window(
    *,
    task_count: int,
    duration_minutes: int,
    degrade_ratio: float,
) -> dict[str, bool | float | int]:
    meets_minimums = task_count >= 3 and duration_minutes >= 30
    rollback_recommended = degrade_ratio > 0.10
    return {
        "task_count": task_count,
        "duration_minutes": duration_minutes,
        "degrade_ratio": degrade_ratio,
        "meets_minimums": meets_minimums,
        "rollback_recommended": rollback_recommended,
    }
