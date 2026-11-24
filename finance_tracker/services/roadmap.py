"""Сервис для построения последовательной дорожной карты финансовых целей."""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from finance_tracker.config import GOAL_CATALOG


@dataclass
class RoadmapStep:
    goal_id: str
    goal_name: str
    cost: Decimal
    months_needed: int
    cumulative_months: int
    note: str = ""


def build_roadmap(
    selected_goal_ids: list[str], 
    monthly_budget: Decimal, 
    extra_savings: Decimal = Decimal("0")
) -> list[RoadmapStep]:
    """
    Строит последовательную дорожную карту достижения целей.
    
    :param selected_goal_ids: Список ID выбранных целей (напр., ["A2", "A4"])
    :param monthly_budget: Базовый свободный денежный поток в месяц
    :param extra_savings: Дополнительная экономия в месяц (из блока оптимизации)
    """
    effective_budget = monthly_budget + extra_savings
    if effective_budget <= 0:
        raise ValueError("Итоговый бюджет на цели должен быть больше 0")

    steps = []
    cumulative_months = 0

    # Фильтруем и сортируем цели по приоритету, затем по алфавиту
    valid_goals = [
        (gid, GOAL_CATALOG[gid]) 
        for gid in selected_goal_ids 
        if gid in GOAL_CATALOG
    ]
    sorted_goals = sorted(valid_goals, key=lambda x: (x[1]["priority"], x[0]))

    for goal_id, goal_data in sorted_goals:
        cost = Decimal(str(goal_data["cost"]))
        # Округляем месяцы в большую сторону (нельзя закрыть цель за 0.3 месяца)
        months = int((cost / effective_budget).to_integral_value(rounding=ROUND_CEILING))
        cumulative_months += months
        
        steps.append(RoadmapStep(
            goal_id=goal_id,
            goal_name=goal_data["name"],
            cost=cost,
            months_needed=months,
            cumulative_months=cumulative_months,
            note=goal_data.get("note", "")
        ))

    return steps
