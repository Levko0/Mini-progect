from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# -----------------------------------------------------------
# 1. КОРИСТУВАЧІ ТА ПРОФІЛЬ
# -----------------------------------------------------------
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False) # Логін
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) # Пароль (зашифрований)
    created_at = Column(DateTime, default=datetime.now)

    # Зв'язки з іншими таблицями
    measurements = relationship("UserMeasurement", back_populates="user")
    nutrition_plans = relationship("NutritionPlan", back_populates="user")
    workouts = relationship("WorkoutLog", back_populates="user")

class UserMeasurement(Base):
    """Тут зберігаємо історію ваги та параметрів для аналізу прогресу"""
    __tablename__ = 'user_measurements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now)
    
    weight = Column(Float, nullable=False)   # Вага (для формули BMR)
    height = Column(Float, nullable=False)   # Зріст
    age = Column(Integer, nullable=False)    # Вік
    gender = Column(String, nullable=False)  # 'male'/'female'
    activity_level = Column(Float, default=1.2) # 1.2, 1.55 і т.д.
    goal = Column(String, nullable=False)    # 'loss', 'gain', 'maintain'

    user = relationship("User", back_populates="measurements")

# -----------------------------------------------------------
# 2. ХАРЧУВАННЯ (Результати алгоритму)
# -----------------------------------------------------------
class NutritionPlan(Base):
    """Сюди записуємо те, що нарахував скрипт (BMR, TDEE, Macros)"""
    __tablename__ = 'nutrition_plans'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)

    daily_calories = Column(Integer) # Цільові калорії (TDEE_adj)
    protein_g = Column(Float)        # Білки в грамах
    fat_g = Column(Float)            # Жири
    carbs_g = Column(Float)          # Вуглеводи

    user = relationship("User", back_populates="nutrition_plans")

# -----------------------------------------------------------
# 3. ТРЕНУВАННЯ (Бібліотека та Логи)
# -----------------------------------------------------------
class Exercise(Base):
    """Бібліотека вправ (Довідник)"""
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)       # Назва (напр. "Жим лежачи")
    category = Column(String)                   # 'cardio', 'strength'
    difficulty = Column(String)                 # 'easy', 'hard'
    description = Column(String)                # Опис техніки

class WorkoutLog(Base):
    """Щоденник тренувань: факт виконання"""
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.now)
    notes = Column(String)             # Коментар ("Було важко")
    duration_minutes = Column(Integer) # Скільки тривало тренування

    # Зв'язок "багато-до-багатьох" або деталі можна реалізувати окремою таблицею
    user = relationship("User", back_populates="workouts")


# -----------------------------------------------------------
# 4. Створення файлу бази даних
# -----------------------------------------------------------
engine = create_engine('sqlite:///fitness_app.db')

Base.metadata.create_all(engine)

print("Базу даних 'fitness_app.db' успішно створено!")
