from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# Таблиця для збереження тренувань
class Workout(Base):
    __tablename__ = 'workouts'
    id = Column(Integer, primary_key=True)
    date = Column(String)
    type = Column(String)
    duration = Column(Integer)
    load = Column(Float)

# Таблиця для збереження даних з калькулятора (профілі)
class UserProfile(Base):
    __tablename__ = 'user_profiles'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    weight = Column(Float)
    height = Column(Float)
    age = Column(Integer)
    gender = Column(String)
    goal = Column(String)
    pal = Column(Float)

# ОСЬ ТУТ ЗМІНЕНО НАЗВУ БАЗИ НА fitness_app.db
engine = create_engine('sqlite:///fitness_app.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)