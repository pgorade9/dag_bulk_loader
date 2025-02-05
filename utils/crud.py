# from sqlalchemy import delete
from sqlmodel import Session, select, delete

from data.database import LoadTest
from models.datamodels import TestSummary


def get_all_tests_for_id(test_id, session: Session):
    return session.exec(select(LoadTest).where(LoadTest.test_id == test_id)).all()


def get_summary(session: Session):
    tests = session.exec(select(LoadTest)).all()
    test_ids = [test.test_id for test in tests]
    unique_test_ids = set(test_ids)
    tests_summary = {}
    for test_id in unique_test_ids:
        count = get_run_count_for_test_id(test_id, session)
        workflow_id = session.exec(select(LoadTest).where(LoadTest.test_id==test_id)).first().workflow_name
        test_summary = TestSummary(test_id=test_id, run_count=count, workflow_name=workflow_id)
        tests_summary.update({test_id: test_summary})
    return tests_summary


def get_run_count_for_test_id(test_id, session):
    tests_for_id = get_all_tests_for_id(test_id, session)
    count = len(tests_for_id)
    return count


def clear_database(session: Session):
    session.exec(delete(LoadTest))
    session.commit()
    return {"msg": "database cleared"}
