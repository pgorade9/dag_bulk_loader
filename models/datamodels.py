from pydantic import BaseModel


class TestSummary(BaseModel):
    run_count: int
    workflow_name: str


class TestDetails(BaseModel):
    env: str
    workflow_name: str
    run_count: int
    trigger_timestamp: int


class TestReport(BaseModel):
    env: str
    workflow_name: str
    run_count: int
    trigger_timestamp: int
    success_count: int
    failed_count: int
    success_percentage: float
    failed_percentage: float
    time_taken_minutes: float
