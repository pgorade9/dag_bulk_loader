from sqlalchemy import delete
from sqlmodel import SQLModel, Field, create_engine, Session, select

SQLALCHEMY_DATABASE_URL = "sqlite:///test_db.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# Create an SQLite database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, pool_size=50, max_overflow=50
)


# Define a model (inherits from SQLModel)
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None


# Create the table
SQLModel.metadata.create_all(engine)


# insert data into table
def add_hero():
    with Session(engine) as session:
        hero1 = Hero(name="Manthan", secret_name="manthan_jvc", age=12)
        session.add(hero1)
        hero2 = Hero(name="Prashant", secret_name="prash_jvc", age=25)
        session.add(hero2)
        session.commit()
        print("added Hero successfully")


def get_hero():
    with Session(engine) as session:
        results = session.exec(select(Hero)).all()
        for result in results:
            print(result)


def update_hero():
    with Session(engine) as session:
        result = session.exec(select(Hero).where(Hero.age == 25)).first()
        print(result.name)


def clear_db():
    with Session(engine) as session:
        session.exec(delete(Hero))
        session.commit()


if __name__ == "__main__":
    # clear_db()
    # add_hero()
    # get_hero()
    update_hero()
