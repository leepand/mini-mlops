import os
from typing import Optional
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session, Field
from mlopskit.utils.file_utils import path_to_local_sqlite_uri
from datetime import datetime


SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL", path_to_local_sqlite_uri("sql_app.db")
)


class SQLiteData:
    def __init__(self, db_name=None, init_db=False):
        load_dotenv()  # take environment variables from .env.
        if db_name is None:
            self.db_url = SQLALCHEMY_DATABASE_URL
        else:
            self.db_url = path_to_local_sqlite_uri(db_name)
        if init_db:
            self.build()

    # Create engine
    def build(self):
        self.engine = create_engine(self.db_url, echo=True)
        # Creates all the tables defined in models module
        SQLModel.metadata.create_all(self.engine)

    # Connet to database
    def get_db(self):
        db = Session(self.engine)
        try:
            yield db
        finally:
            db.close()

    def store_data(self, data):
        with Session(self.engine) as session:
            session.add(data)
            session.commit()
            session.refresh(data)
        return data

    def query_data(self, query):
        with Session(self.engine) as session:
            results = session.execute(query)
            for row in results:
                w = dict(row._mapping.items())
                yield (w)


class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    class Config:
        schema_extra = {}
