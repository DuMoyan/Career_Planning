"""SQLAlchemy 持久化模型。"""

from app.models.ai_run import AIPlanningRun
from app.models.goal import CareerGoal
from app.models.target import CareerTarget, CareerTargetRequirement

__all__ = ["AIPlanningRun", "CareerGoal", "CareerTarget", "CareerTargetRequirement"]
