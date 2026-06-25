"""
Statistics service: aggregate data from database.
No hardcoded fallback data — empty DB returns empty lists.
"""
from typing import List
from app.services.models import StatsOverview, LevelStat, WeaknessStat, DayStat
from app.services import database as db


class StatsService:
    """Aggregate practice statistics from database."""

    def get_overview(self) -> StatsOverview:
        return db.get_stats_overview()

    def get_by_level(self) -> List[LevelStat]:
        return db.get_level_stats()

    def get_by_weakness(self) -> List[WeaknessStat]:
        return db.get_weakness_stats()

    def get_trend(self, days: int = 30) -> List[DayStat]:
        return db.get_daily_trend(days)
