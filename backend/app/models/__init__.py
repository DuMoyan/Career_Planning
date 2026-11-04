"""SQLAlchemy 持久化模型。"""

from app.models.goal import CareerGoal
from app.models.target import CareerTarget, CareerTargetRequirement

__all__ = ["CareerGoal", "CareerTarget", "CareerTargetRequirement"]
