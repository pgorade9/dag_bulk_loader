from pydantic import BaseModel


class TestSummary(BaseModel):
    run_count: int
    workflow_name: str


class TestDetails(BaseModel):
    env: str
    workflow_name: str
    run_count: int
    trigger_timestamp: int
