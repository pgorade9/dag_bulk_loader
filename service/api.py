from enum import Enum
from typing import List

import pandas as pd
from fastapi import APIRouter, Query, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session

from data.database import engine
from models.datamodels import TestDetails, TestReport
from utils import crud
from utils.crud import get_summary, clear_database
from .workflow_service import load, async_status, get_test_details, generate_report

router = APIRouter()


def get_session():
    with Session(engine) as session:  # ✅ Automatically closes session after use
        yield session


@router.get("/load")
def bulk_loader(
        env: str = Query(None, description="Environment value",
                         enum=["evt-ltops", "adme-outerloop", "mde-ltops", "prod-canary-ltops", "prod-aws-ltops",
                               "prod-qanoc-ltops"]),
        dag: str = Query(None, description="DAG name",
                         enum=["csv_parser_wf_status_gsm", "wellbore_ingestion_wf_gsm", "doc_ingestor_azure_ocr_wf",
                               "shapefile_ingestor_wf_status_gsm"]),
        count: int = Query(1, description="Number of items to process"),
        session: Session = Depends(get_session)):
    return load(env, dag, count, session)


@router.get("/export-excel/{test_id}")
def export_to_excel(test_id: str, session: Session = Depends(get_session)):
    """Fetch all test units and save them to an Excel file."""

    # Fetch all data
    tests = crud.get_all_tests_for_id(test_id, session)

    if not tests:
        return {"message": "No data available to export"}

    # Convert to pandas DataFrame
    data = [test.dict() for test in tests]  # Convert to dict format
    column_order=['id','env_name', 'workflow_name','test_id','run_id','correlation_id',
                  'submitted_timestamp','success_timestamp','failed_timestamp']
    df = pd.DataFrame(data)
    df = df[column_order]

    # Define file path
    file_path = "tests_data.xlsx"
    df.to_excel(file_path, index=False)  # Save to Excel file

    return FileResponse(file_path, filename="load_test_data.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/summary")
def summary(session: Session = Depends(get_session)):
    return get_summary(session)


@router.get("/clear_db")
def clear_db(session: Session = Depends(get_session)):
    return clear_database(session)


@router.get("/update_status/{test_id}")
async def update_status(test_id: str, session: Session = Depends(get_session)):
    return await async_status(test_id, session)


@router.get("/test_details/{test_id}", response_model=TestDetails)
def test_details(test_id: str, session: Session = Depends(get_session)):
    return get_test_details(test_id, session)


@router.get("/report/{test_id}", response_model=TestReport)
async def report(test_id: str, session: Session = Depends(get_session)):
    return await generate_report(test_id, session)
