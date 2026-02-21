from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import csv, io

from models import Base, User, UserMeasurement, NutritionPlan, Exercise, WorkoutLog
from algorithm import FitnessUser

app = Flask(__name__)
app.secret_key = 'your-secret-key'
CORS(app, supports_credentials=True)

engine = create_engine('sqlite:///fitness_app.db')
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)


# ═══════════════════════════════════════════════════
# ООП: БАЗОВІ КЛАСИ
# ═══════════════════════════════════════════════════

class BaseHandler:
    def get_db(self): return DBSession()
    def current_user_id(self): return session.get('user_id')
    def ok(self, data, code=200): return jsonify(data), code
    def error(self, msg, code=400): return jsonify({'error': msg}), code
    def handle(self): raise NotImplementedError


class ProtectedHandler(BaseHandler):
    def handle(self):
        if not self.current_user_id():
            return self.error('Не авторизовано', 401)
        return self.handle_protected()

    def handle_protected(self): raise NotImplementedError

    def _get_last_measurement(self, db):
        return (db.query(UserMeasurement)
                .filter_by(user_id=self.current_user_id())
                .order_by(UserMeasurement.date.desc()).first())

    def _build_fitness_user(self, m):
        return FitnessUser('', m.weight, m.height, m.age, m.gender, m.goal, m.activity_level)

    def _save_nutrition_plan(self, db, fu):
        fu.calculate_nutrition()
        plan = NutritionPlan(
            user_id=self.current_user_id(),
            daily_calories=round(fu.tdee_adj),
            protein_g=fu.macros.get('protein', 0),
            fat_g=fu.macros.get('fat', 0),
            carbs_g=fu.macros.get('carbs', 0)
        )
        db.add(plan)
        return plan


# ═══════════════════════════════════════════════════
# API HANDLERS
# ═══════════════════════════════════════════════════

class RegisterHandler(BaseHandler):
    def handle(self):
        data = request.json
        db = self.get_db()
        if db.query(User).filter_by(email=data['email']).first():
            return self.error('Email вже зареєстровано')
        user = User(username=data['username'], email=data['email'],
                    password_hash=generate_password_hash(data['password']))
        db.add(user); db.commit()
        session['user_id'] = user.id
        return self.ok({'message': 'Реєстрація успішна'}, 201)


class LoginHandler(BaseHandler):
    def handle(self):
        data = request.json
        db = self.get_db()
        user = db.query(User).filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password_hash, data['password']):
            return self.error('Невірний email або пароль', 401)
        session['user_id'] = user.id
        return self.ok({'message': 'Вхід успішний'})


class LogoutHandler(BaseHandler):
    def handle(self):
        session.clear()
        return self.ok({'message': 'Вийшли'})


class SaveMeasurementsHandler(ProtectedHandler):
    def handle_protected(self):
        data = request.json
        db = self.get_db()
        db.add(UserMeasurement(user_id=self.current_user_id(), date=date.today(),
            weight=data['weight'], height=data['height'], age=data['age'],
            gender=data['gender'], activity_level=data.get('activity_level', 1.2), goal=data['goal']))
        fu = FitnessUser('', data['weight'], data['height'], data['age'],
                         data['gender'], data['goal'], data.get('activity_level', 1.2))
        plan = self._save_nutrition_plan(db, fu)
        db.commit()
        fu.update_training_plan() # Оновлюємо план
        return self.ok({'daily_calories': plan.daily_calories, 'protein_g': plan.protein_g,
                        'fat_g': plan.fat_g, 'carbs_g': plan.carbs_g,
                        'recommendation': fu.training.get('type')}, 201) # Беремо тип тренування


class LogWorkoutHandler(ProtectedHandler):
    def handle_protected(self):
        data = request.json
        db = self.get_db()

        # Додаємо тренування
        workout = WorkoutLog(
            user_id=self.current_user_id(),
            date=datetime.now(),
            notes=data.get('notes', ''),
            duration_minutes=data.get('duration_minutes', 0)
        )
        db.add(workout)

        # ОНОВЛЕННЯ STREAK ← НОВИЙ КОД
        self._update_streak(db, self.current_user_id(), workout.date)

        progress = None
        if 'weight' in data and data['weight']:
            m = self._get_last_measurement(db)
            if m:
                fu = self._build_fitness_user(m)
                from algorithm import ProgressAnalyzer
                progress = ProgressAnalyzer.analyze(fu, data['weight'])
                db.add(UserMeasurement(user_id=self.current_user_id(), date=date.today(),
                    weight=data['weight'], height=m.height, age=m.age,
                    gender=m.gender, activity_level=m.activity_level, goal=m.goal))

        db.commit()
        return self.ok({'message': 'Тренування записано!', 'progress': progress}, 201)

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

        training_rec, overtraining = None, None
        training_rec, overtraining = None, None
        if m:
            fu = self._build_fitness_user(m)
            fu.update_training_plan() # Оновлюємо план
            training_rec = fu.training.get('type') # Беремо тип тренування
            # overtraining = fu.check_overtraining(workouts_count) # ВИДАЛЯЄМО, бо цього методу більше немає

        return self.ok({
            'user': user.username,
            'measurement': {'weight': m.weight, 'goal': m.goal} if m else None,
            'plan': {'daily_calories': plan.daily_calories, 'protein_g': plan.protein_g,
                     'fat_g': plan.fat_g, 'carbs_g': plan.carbs_g} if plan else None,
            'workouts': [{'date': str(w.date)[:10], 'notes': w.notes,
                          'duration': w.duration_minutes} for w in workouts],
            'total_workouts': workouts_count,
            'recommendation': training_rec,
            'overtraining': overtraining
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


# ═══════════════════════════════════════════════════
# ═══════════════════════════════════════════════════
# МАРШРУТИ
# ═══════════════════════════════════════════════════

@app.route('/')
def dashboard_page():    return render_template_string(HTML_DASHBOARD)

@app.route('/login')
def login_page():        return render_template_string(HTML_LOGIN)

@app.route('/register')
def register_page():     return render_template_string(HTML_REGISTER)

@app.route('/exercises')
def exercises_page():    return render_template_string(HTML_EXERCISES)

@app.route('/api/register',             methods=['POST'])
def register():          return RegisterHandler().handle()

@app.route('/api/login',                methods=['POST'])
def login():             return LoginHandler().handle()

@app.route('/api/logout',               methods=['POST'])
def logout():            return LogoutHandler().handle()

@app.route('/api/profile/measurements', methods=['POST'])
def save_measurements(): return SaveMeasurementsHandler().handle()

@app.route('/api/workouts/log',         methods=['POST'])
def log_workout():       return LogWorkoutHandler().handle()

@app.route('/api/progress/analyze',     methods=['POST'])
def analyze_progress():  return ProgressAnalysisHandler().handle()

@app.route('/api/tracker/import',       methods=['POST'])
def import_tracker():    return TrackerImportHandler().handle()

@app.route('/api/dashboard',            methods=['GET'])
def dashboard_api():     return DashboardHandler().handle()

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():       return LeaderboardHandler().handle()

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

@app.route('/library') # Хлопці назвали файл library.html, краще назвати маршрут так само
def library_page():
    return render_template('library.html')

@app.route('/calculator') # Додаємо маршрут для їхнього калькулятора
def calculator_page():
    return render_template('calculator.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

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
