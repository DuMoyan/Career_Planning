from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.report import WeeklyReportCreate


def test_week_start_must_be_monday() -> None:
    assert WeeklyReportCreate(week_start=date(2026, 11, 2)).week_start.weekday() == 0

    with pytest.raises(ValidationError, match="周一"):
        WeeklyReportCreate(week_start=date(2026, 11, 1))
