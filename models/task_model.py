from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine("sqlite:///tasks.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    priority = Column(Integer)
    due_date = Column(Date)
    status = Column(String)
    category = Column(String, default="Общо")

Base.metadata.create_all(bind=engine)
