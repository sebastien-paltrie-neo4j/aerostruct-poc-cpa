from typing import Literal

from pydantic import BaseModel


class Task(BaseModel):
    id: str
    name: str
    start: str
    end: str
    dependencies: str
    isCritical: bool
    isIncident: bool
    duration_days: float


class GanttResponse(BaseModel):
    tasks: list[Task]
    criticalPath: list[str]
    totalDuration: float
    sink: str | None
    incidentWo: str | None = None
    delayDays: float = 0
    backend: Literal["cypher", "gds"] | None = None
