<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from algotitm import FitnessUser 
from models import Session, Workout, UserProfile # Підключаємо базу даних
=======
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import csv, io


from sqlalchemy import func
from models import Base, User, UserMeasurement, NutritionPlan, Exercise, WorkoutLog, FoodLog
from algorithm import FitnessUser
>>>>>>> origin/new-backend-and-frontend

app = Flask(__name__)

NEW_IMAGE_URL = "https://tovarystvo-kraftu.com/content/uploads/images/yajtsia-kuriache-tsesarky-perepelyne.png"

EXERCISE_DB = {
    "Кардіо": [
        {"name": "Біг", "desc": "Інтервальний біг 30/30 сек.", "img": NEW_IMAGE_URL},
        {"name": "Велосипед", "desc": "Середній темп 45 хв.", "img": NEW_IMAGE_URL},
        {"name": "Скакалка", "desc": "Інтенсивні стрибки 15 хв.", "img": NEW_IMAGE_URL}
    ],
    "Силові": [
        {"name": "Жим лежачи", "desc": "3 підходи по 10 повторень.", "img": NEW_IMAGE_URL},
        {"name": "Присідання", "desc": "4 підходи по 12 повторень.", "img": NEW_IMAGE_URL},
        {"name": "Тяга штанги", "desc": "3 підходи по 8 повторень.", "img": NEW_IMAGE_URL}
    ],
    "Спорт": [
        {"name": "Волейбол", "desc": "Ігрова практика.", "img": NEW_IMAGE_URL},
        {"name": "Баскетбол", "desc": "Кидки в кільце 30 хв.", "img": NEW_IMAGE_URL},
        {"name": "Плавання", "desc": "Кроль 1000м.", "img": NEW_IMAGE_URL}
    ]
}

def get_stats(db_session):
    # Дістаємо всі тренування з бази даних
    all_workouts = db_session.query(Workout).all()
    
    total_load = sum(w.load for w in all_workouts if w.load)
    count = len(all_workouts)
    
    return {
        "total": round(total_load, 1),
        "count": count,
        "chart_labels": [w.date for w in all_workouts[-7:]],
        "chart_data": [w.load for w in all_workouts[-7:]]
    }

def calculate_load(duration, intensity):
    try:
        d = float(duration)
        i = float(intensity)
        return round(d * i * 0.1, 1)
    except:
        return 0

@app.route("/", methods=["GET", "POST"])
def dashboard():
    db = Session() # Відкриваємо зв'язок з БД
    
    if request.method == "POST":
        # Зберігаємо нове тренування в базу даних
        new_workout = Workout(
            date=request.form.get("date"),
            type=request.form.get("type"),
            duration=int(request.form.get("duration", 0)),
            load=calculate_load(request.form.get("duration"), request.form.get("intensity"))
        )
        db.add(new_workout)
        db.commit()
        db.close()
        return redirect(url_for("dashboard"))
    
    # Витягуємо тренування (від найновіших до найстаріших)
    workouts = db.query(Workout).order_by(Workout.id.desc()).all()
    stats = get_stats(db)
    db.close()
    
    return render_template("dashboard.html", stats=stats, workouts=workouts, today=datetime.now().strftime('%Y-%m-%d'))

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            weight = float(request.form.get("weight"))
            height = float(request.form.get("height"))
            age = int(request.form.get("age"))
            gender = request.form.get("gender")
            goal = request.form.get("goal")
            pal = float(request.form.get("pal"))

            # Зберігаємо введені користувачем дані в базу даних
            db = Session()
            new_profile = UserProfile(
                name=name, weight=weight, height=height, age=age, 
                gender=gender, goal=goal, pal=pal
            )
            db.add(new_profile)
            db.commit()
            db.close()

            user = FitnessUser(name, weight, height, age, gender, goal, pal)
            return render_template("result.html", plan=user.get_full_plan())

        except ValueError:
            return "Помилка! Введіть коректні числа.", 400

    return render_template("calculator.html")

@app.route("/library")
def library():
    return render_template("library.html", exercises=EXERCISE_DB)

<<<<<<< HEAD
if __name__ == "__main__":
    app.run(debug=True, port=5000)
=======
    # НОВА ФУНКЦІЯ ДЛЯ STREAK
    def _update_streak(self, db, user_id, workout_date):
        """Оновлює streak користувача"""
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return

        # Перетворюємо в date якщо datetime
        if isinstance(workout_date, datetime):
            workout_date = workout_date.date()

        # Перше тренування
        if user.last_workout_date is None:
            user.current_streak = 1
            user.best_streak = 1
            user.total_workouts = 1
            user.last_workout_date = workout_date
            return

        # Різниця в днях
        days_diff = (workout_date - user.last_workout_date).days

        if days_diff == 0:
            # Те саме день - тільки лічильник
            user.total_workouts += 1
        elif days_diff == 1:
            # Вчора - продовжуємо серію
            user.current_streak += 1
            user.total_workouts += 1
            user.last_workout_date = workout_date

            if user.current_streak > user.best_streak:
                user.best_streak = user.current_streak
        else:
            # Пропуск - почати спочатку
            user.current_streak = 1
            user.total_workouts += 1
            user.last_workout_date = workout_date


class DashboardHandler(ProtectedHandler):
    def handle_protected(self):
        db = self.get_db()
        uid = self.current_user_id()
        user = db.query(User).filter_by(id=uid).first()
        m = self._get_last_measurement(db)
        plan = (db.query(NutritionPlan).filter_by(user_id=uid)
                .order_by(NutritionPlan.created_at.desc()).first())
        workouts = (db.query(WorkoutLog).filter_by(user_id=uid)
                    .order_by(WorkoutLog.date.desc()).limit(5).all())
        workouts_count = db.query(WorkoutLog).filter_by(user_id=uid).count()

        # НОВЕ: Рахуємо скільки калорій з'їдено за сьогодні
        consumed_today = db.query(func.sum(FoodLog.calories)).filter(
            FoodLog.user_id == uid,
            FoodLog.date == date.today()
        ).scalar() or 0

        training_rec, overtraining = None, None
        if m:
            fu = self._build_fitness_user(m)
            fu.update_training_plan() # Оновлюємо план
            training_rec = fu.training.get('type') # Беремо тип тренування

        return self.ok({
            'user': user.username,
            'measurement': {'weight': m.weight, 'goal': m.goal} if m else None,
            'plan': {'daily_calories': plan.daily_calories, 'protein_g': plan.protein_g,
                     'fat_g': plan.fat_g, 'carbs_g': plan.carbs_g} if plan else None,
            'workouts': [{'date': str(w.date)[:10], 'notes': w.notes,
                          'duration': w.duration_minutes} for w in workouts],
            'total_workouts': workouts_count,
            'recommendation': training_rec,
            'consumed_today': consumed_today # Передаємо на фронтенд
        })

class LeaderboardHandler(BaseHandler):
    def handle(self):
        sort_by = request.args.get('sort_by', 'current_streak')
        limit = int(request.args.get('limit', 10))

        db = self.get_db()

        # Вибираємо поле сортування
        if sort_by == 'best_streak':
            order_field = User.best_streak
        elif sort_by == 'total_workouts':
            order_field = User.total_workouts
        else:
            order_field = User.current_streak

        # Топ користувачів
        top_users = (db.query(User)
                     .filter(User.total_workouts > 0)
                     .order_by(order_field.desc())
                     .limit(limit)
                     .all())

        leaderboard = []
        for rank, user in enumerate(top_users, start=1):
            leaderboard.append({
                'rank': rank,
                'username': user.username,
                'current_streak': user.current_streak,
                'best_streak': user.best_streak,
                'total_workouts': user.total_workouts,
                'last_workout': str(user.last_workout_date) if user.last_workout_date else None
            })

        return self.ok({'leaderboard': leaderboard, 'sort_by': sort_by})

class ProgressAnalysisHandler(ProtectedHandler):
    def handle_protected(self):
        data = request.json
        db = self.get_db()
        m = self._get_last_measurement(db)
        if not m: return self.error('Немає вимірів', 404)
        fu = self._build_fitness_user(m)
        from algorithm import ProgressAnalyzer
        analysis = ProgressAnalyzer.analyze(fu, data['new_weight']) # У LogWorkoutHandler там data['weight']
        fu.weight = data['new_weight']
        plan = self._save_nutrition_plan(db, fu)
        db.add(UserMeasurement(user_id=self.current_user_id(), date=date.today(),
            weight=data['new_weight'], height=m.height, age=m.age,
            gender=m.gender, activity_level=m.activity_level, goal=m.goal))
        db.commit()
        return self.ok({'analysis': analysis, 'delta': round(data['new_weight'] - m.weight, 1),
                        'new_calories': plan.daily_calories})


class TrackerImportHandler(ProtectedHandler):
    def handle_protected(self):
        if 'file' not in request.files: return self.error('Файл не знайдено')
        content = request.files['file'].read().decode('utf-8')
        records = [{'steps': int(r['steps']), 'active_calories': float(r['active_calories'])}
                   for r in csv.DictReader(io.StringIO(content))]
        if not records: return self.error('CSV порожній')
        avg = sum(r['steps'] for r in records) / len(records)
        pal, label = (1.725, 'Дуже активний') if avg >= 12000 else \
                     (1.55,  'Помірно активний') if avg >= 10000 else \
                     (1.375, 'Легка активність') if avg >= 7500 else (1.2, 'Малоактивний')
        db = self.get_db()
        m = self._get_last_measurement(db)
        if m:
            fu = self._build_fitness_user(m); fu.pal = pal
            self._save_nutrition_plan(db, fu); db.commit()
        return self.ok({'avg_steps': round(avg), 'activity_level': label, 'new_pal': pal})

class SettingsHandler(ProtectedHandler):###
    def handle_protected(self):
        data = request.json
        db = self.get_db()
        user = db.query(User).filter_by(id=self.current_user_id()).first()

        if not user:
            return self.error('Користувача не знайдено', 404)

        # Якщо користувач передав нове ім'я
        if 'new_username' in data and data['new_username']:
            # Перевірка, чи не зайняте ім'я
            existing_user = db.query(User).filter_by(username=data['new_username']).first()
            if existing_user and existing_user.id != user.id:
                return self.error('Це ім\'я вже зайняте іншим користувачем')
            user.username = data['new_username']

        # Якщо користувач передав новий пароль
        if 'new_password' in data and data['new_password']:
            user.password_hash = generate_password_hash(data['new_password'])

        db.commit()
        return self.ok({'message': 'Налаштування успішно оновлено!'})

class LogFoodHandler(ProtectedHandler):
    def handle_protected(self):
        data = request.json
        db = self.get_db()

        food = FoodLog(
            user_id=self.current_user_id(),
            date=date.today(),
            calories=int(data.get('calories', 0)),
            meal_name=data.get('meal_name', 'Прийом їжі')
        )
        db.add(food)
        db.commit()
        return self.ok({'message': 'Калорії збережено!'}, 201)

# ═══════════════════════════════════════════════════
# МАРШРУТИ (Оновлено під нові файли)
# ═══════════════════════════════════════════════════

@app.route('/')
def dashboard_page():
    # Замість render_template_string тепер використовуємо render_template
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/library')
def library_page():
    db = DBSession()
    all_exercises = db.query(Exercise).all()

    # Групуємо вправи за категоріями, як цього чекає library.html
    from collections import defaultdict
    exercises_dict = defaultdict(list)

    for ex in all_exercises:
        exercises_dict[ex.category].append({
            "name": ex.name,
            "desc": ex.description,
            "video_url": ex.video_url, # Передаємо відео
            "img": "https://cdn-icons-png.flaticon.com/512/2964/2964514.png" # Дефолтна картинка-заглушка
        })

    return render_template('library.html', exercises=exercises_dict)

@app.route('/calculator') # Додаємо маршрут для їхнього калькулятора
def calculator_page():
    return render_template('calculator.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

@app.route('/api/food/log', methods=['POST'])
def log_food(): return LogFoodHandler().handle()

# --- API МАРШРУТИ ЗАЛИШАЄМО БЕЗ ЗМІН! ---
# Вони відповідають за логіку, базу даних і розрахунки.

@app.route('/api/register',             methods=['POST'])
def register():          return RegisterHandler().handle()

@app.route('/api/login',                methods=['POST'])
def login():             return LoginHandler().handle()

@app.route('/api/logout',               methods=['POST'])
def logout():            return LogoutHandler().handle()

# ... і так далі до кінця файлу

if __name__ == '__main__':
    app.run(debug=True, port=5000)
>>>>>>> origin/new-backend-and-frontend
