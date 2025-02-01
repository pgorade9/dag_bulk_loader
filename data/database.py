import uuid
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine, Session, select, delete

# global config
SQLALCHEMY_DATABASE_URL = "sqlite:///data/workflow.db"

# Module testing config
# SQLALCHEMY_DATABASE_URL = "sqlite:///workflow.db"

# Create an SQLite database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, pool_size=50, max_overflow=50
)


# Define a model (inherits from SQLModel)
class LoadTest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    test_id: str
    correlation_id: str
    run_id: str
    # workflow_status: str
    submitted_timestamp: Optional[int] = None
    success_timestamp: Optional[int] = None
    failed_timestamp: Optional[int] = None
    workflow_name:str
    env_name: str


# Create the table
SQLModel.metadata.create_all(engine)


# insert data into table
def add_hero():
    with Session(engine) as session:
        test_unit = LoadTest(test_id=str(uuid.uuid4()),
                             correlation_id=str(uuid.uuid4()),
                             run_id=str(uuid.uuid4()),
                             workflow_status="submitted",
                             timestamp=1738326219320)
        session.add(test_unit)
        session.commit()
        print("added test_unit successfully")


def get_hero():
    with Session(engine) as session:
        results = session.exec(select(LoadTest)).all()
        for result in results:
            print(result)


def clear_db():
    with Session(engine) as session:
        session.exec(delete(LoadTest))
        session.commit()


if __name__ == "__main__":
    clear_db()
    # add_hero()
    # get_hero()
