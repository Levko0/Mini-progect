from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# -----------------------------------------------------------
# 1. КОРИСТУВАЧІ ТА ПРОФІЛЬ (БЕЗ ЗМІН)
# -----------------------------------------------------------
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    total_workouts = Column(Integer, default=0)
    last_workout_date = Column(Date, nullable=True)

    measurements = relationship("UserMeasurement", back_populates="user")
    nutrition_plans = relationship("NutritionPlan", back_populates="user")
    workouts = relationship("WorkoutLog", back_populates="user")
    feedbacks = relationship("WorkoutFeedback", back_populates="user")
    training_plans = relationship("TrainingPlan", back_populates="user")
    checkins = relationship("BiweeklyCheck", back_populates="user")


class UserMeasurement(Base):
    __tablename__ = 'user_measurements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    activity_level = Column(Float, default=1.2)
    goal = Column(String, nullable=False)

    user = relationship("User", back_populates="measurements")

# -----------------------------------------------------------
# 2. ХАРЧУВАННЯ (БЕЗ ЗМІН)
# -----------------------------------------------------------
class NutritionPlan(Base):
    __tablename__ = 'nutrition_plans'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    daily_calories = Column(Integer)
    protein_g = Column(Float)
    fat_g = Column(Float)
    carbs_g = Column(Float)

    user = relationship("User", back_populates="nutrition_plans")

# -----------------------------------------------------------
# 3. ТРЕНУВАННЯ (БЕЗ ЗМІН)
# -----------------------------------------------------------
class Exercise(Base):
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    difficulty = Column(String)
    description = Column(String)
    is_essential = Column(Boolean, default=False)
    day_number   = Column(Integer, nullable=True)
    video_url    = Column(String, nullable=True)

class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.now)
    notes = Column(String)             # тип тренування
    duration_minutes = Column(Integer)

    user = relationship("User", back_populates="workouts")
    feedback = relationship("WorkoutFeedback", back_populates="workout", uselist=False)

# -----------------------------------------------------------
# 4. НОВЕ: ВІДГУК ПІСЛЯ ТРЕНУВАННЯ
# -----------------------------------------------------------
class WorkoutFeedback(Base):
    """Самопочуття та вправи після кожного тренування"""
    __tablename__ = 'workout_feedbacks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    workout_id = Column(Integer, ForeignKey('workout_logs.id'), unique=True)
    created_at = Column(DateTime, default=datetime.now)

    feeling = Column(Integer, nullable=False)   # 1-5: як почувався
    energy = Column(Integer)                    # 1-5: рівень енергії
    exercises_done = Column(Text)               # список вправ через кому
    comment = Column(Text)                      # вільний коментар

    user = relationship("User", back_populates="feedbacks")
    workout = relationship("WorkoutLog", back_populates="feedback")

# -----------------------------------------------------------
# 5. НОВЕ: ПРОГРАМА ТРЕНУВАНЬ
# -----------------------------------------------------------
class TrainingPlan(Base):
    """Програма тренувань, згенерована після калькулятора"""
    __tablename__ = 'training_plans'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    goal = Column(String)                       # loss / gain / maintain
    days_per_week = Column(Integer)             # к-сть тренувань на тиждень
    plan_json = Column(Text)                    # JSON з планом по днях
    is_active = Column(Boolean, default=True)   # чи актуальний план

    user = relationship("User", back_populates="training_plans")

# -----------------------------------------------------------
# 6. НОВЕ: ЗАМІРИ РАЗ В 2 ТИЖНІ
# -----------------------------------------------------------
class BiweeklyCheck(Base):
    """Контрольні заміри кожні 2 тижні для аналізу прогресу"""
    __tablename__ = 'biweekly_checks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now)

    weight = Column(Float, nullable=False)
    waist_cm = Column(Float)                    # талія
    chest_cm = Column(Float)                    # груди
    hips_cm = Column(Float)                     # стегна

    avg_energy = Column(Integer)                # середня енергія за 2 тижні (1-5)
    workouts_completed = Column(Integer)        # скільки тренувань зроблено
    workouts_planned = Column(Integer)          # скільки було заплановано

    # Рекомендація алгоритму
    recommendation = Column(Text)              # текст: "продовжуй", "збільш навантаження" тощо
    change_needed = Column(Boolean, default=False)

    user = relationship("User", back_populates="checkins")

# -----------------------------------------------------------
# 7. Створення БД
# -----------------------------------------------------------
engine = create_engine('sqlite:///fitness_app.db')
Base.metadata.create_all(engine)
print("Базу даних 'fitness_app.db' успішно створено!")
