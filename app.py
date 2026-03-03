from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from datetime import datetime, date, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from algorithm import FitnessUser
from models import (Base, engine, User, UserMeasurement, NutritionPlan,
                    WorkoutLog, WorkoutFeedback, TrainingPlan, BiweeklyCheck)
from sqlalchemy.orm import sessionmaker, joinedload
import csv, io, json

app = Flask(__name__)
app.secret_key = "activetracker-secret-key"
Session = sessionmaker(bind=engine)

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

TYPE_ALIASES = {
    "run": "Біг", "running": "Біг", "біг": "Біг", "бег": "Біг",
    "gym": "Зал", "strength": "Зал", "зал": "Зал", "weightlifting": "Зал",
    "sport": "Спорт", "спорт": "Спорт",
    "cycling": "Велосипед", "bike": "Велосипед", "велосипед": "Велосипед",
    "swimming": "Спорт", "swim": "Спорт", "плавання": "Спорт",
    "walking": "Біг", "walk": "Біг",
}

EXERCISES_BY_TYPE = {
    "Біг":       ["Біг підтюпцем", "Інтервальний біг", "Ходьба", "Спринт", "Гірський біг"],
    "Зал":       ["Жим лежачи", "Присідання", "Станова тяга", "Підтягування", "Жим плечей",
                  "Тяга блоку", "Планка", "Скручування", "Випади", "Гіперекстензія"],
    "Спорт":     ["Волейбол", "Баскетбол", "Плавання", "Футбол", "Теніс", "Бокс"],
    "Велосипед": ["Їзда на велосипеді", "Велотренажер", "Гірський велосипед"],
    "default":   ["Розминка", "Розтяжка", "Кардіо", "Силові вправи", "Йога", "Пілатес"],
}

# ─── MIDDLEWARE ДЛЯ АВТОРИЗАЦІЇ ───────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def normalize_type(raw):
    if not raw:
        return "Спорт"
    return TYPE_ALIASES.get(raw.strip().lower(), raw.strip().capitalize())

def calculate_load(duration, intensity=3):
    try:
        return round(float(duration) * float(intensity) * 0.1, 1)
    except:
        return 0

def get_stats(db, user_id):
    workouts = db.query(WorkoutLog).filter_by(user_id=user_id).all()
    loads = [round((w.duration_minutes or 0) * 0.3, 1) for w in workouts]
    return {
        "total": round(sum(loads), 1),
        "count": len(workouts),
        "chart_labels": [str(w.date)[:10] for w in workouts[-7:]],
        "chart_data": loads[-7:]
    }

def days_until_checkin(db, user_id):
    last = db.query(BiweeklyCheck).filter_by(user_id=user_id)\
             .order_by(BiweeklyCheck.id.desc()).first()
    if not last:
        return 0
    return max(0, 14 - (date.today() - last.date).days)

def generate_training_plan(goal, pal):
    if pal <= 1.2:
        days = 3
    elif pal <= 1.55:
        days = 4
    else:
        days = 5

    plans = {
        "loss": {
            "description": "Акцент на кардіо та спалювання калорій",
            "schedule": [
                {"day": "Понеділок", "type": "Кардіо", "duration": 40,
                 "exercises": ["Біг підтюпцем 20 хв", "Скакалка 10 хв", "Планка 3×60 сек", "Скручування 3×20"]},
                {"day": "Середа", "type": "Зал", "duration": 50,
                 "exercises": ["Присідання 4×15", "Випади 3×12", "Жим лежачи 3×12", "Тяга блоку 3×12", "Планка 3×45 сек"]},
                {"day": "П'ятниця", "type": "Кардіо", "duration": 45,
                 "exercises": ["Інтервальний біг 25 хв", "Велотренажер 15 хв", "Розтяжка 5 хв"]},
                {"day": "Субота", "type": "Зал", "duration": 40,
                 "exercises": ["Станова тяга 3×10", "Підтягування 3×8", "Жим плечей 3×12", "Гіперекстензія 3×15"]},
                {"day": "Неділя", "type": "Кардіо", "duration": 30,
                 "exercises": ["Ходьба 30 хв або плавання 20 хв"]},
            ][:days]
        },
        "gain": {
            "description": "Акцент на силові тренування та набір маси",
            "schedule": [
                {"day": "Понеділок", "type": "Зал", "duration": 60,
                 "exercises": ["Жим лежачи 5×5", "Жим гантелей 4×8", "Розводка 3×12", "Трицепс на блоці 3×12"]},
                {"day": "Вівторок", "type": "Зал", "duration": 60,
                 "exercises": ["Присідання 5×5", "Жим ногами 4×10", "Розгинання ніг 3×12", "Згинання ніг 3×12"]},
                {"day": "Четвер", "type": "Зал", "duration": 60,
                 "exercises": ["Станова тяга 5×5", "Тяга штанги в нахилі 4×8", "Підтягування 4×6", "Біцепс зі штангою 3×10"]},
                {"day": "Субота", "type": "Зал", "duration": 55,
                 "exercises": ["Жим плечей 4×8", "Тяга штанги до підборіддя 3×10", "Підйом гантелей в сторони 3×12", "Шраги 3×15"]},
                {"day": "Неділя", "type": "Кардіо", "duration": 25,
                 "exercises": ["Легке кардіо 20-25 хв для відновлення"]},
            ][:days]
        },
        "maintain": {
            "description": "Баланс кардіо та силових для підтримки форми",
            "schedule": [
                {"day": "Понеділок", "type": "Зал", "duration": 50,
                 "exercises": ["Жим лежачи 3×10", "Присідання 3×10", "Тяга блоку 3×10", "Планка 3×45 сек"]},
                {"day": "Середа", "type": "Кардіо", "duration": 35,
                 "exercises": ["Біг 20 хв", "Скакалка 10 хв", "Розтяжка 5 хв"]},
                {"day": "П'ятниця", "type": "Зал", "duration": 50,
                 "exercises": ["Станова тяга 3×8", "Підтягування 3×8", "Жим плечей 3×10", "Випади 3×12"]},
                {"day": "Субота", "type": "Кардіо", "duration": 40,
                 "exercises": ["Велосипед або плавання 40 хв"]},
                {"day": "Неділя", "type": "Зал", "duration": 35,
                 "exercises": ["Функціональне тренування або йога 35 хв"]},
            ][:days]
        }
    }

    selected = plans.get(goal, plans["maintain"])
    return {"goal": goal, "days_per_week": days,
            "description": selected["description"], "schedule": selected["schedule"]}

def analyze_checkin(db, user_id, new_weight, workouts_completed, workouts_planned, avg_energy):
    prev = db.query(BiweeklyCheck).filter_by(user_id=user_id)\
             .order_by(BiweeklyCheck.id.desc()).first()
    last_m = db.query(UserMeasurement).filter_by(user_id=user_id)\
               .order_by(UserMeasurement.id.desc()).first()

    goal = last_m.goal if last_m else "maintain"
    change_needed = False
    messages = []

    if prev:
        diff = new_weight - prev.weight
        if goal == "loss":
            if diff < -0.5:
                messages.append("✅ Відмінний прогрес! Вага знижується — продовжуй у тому ж темпі.")
            elif diff > 0.3:
                messages.append("⚠️ Вага зросла. Зменш калорії на 100-150 ккал/день.")
                change_needed = True
            else:
                messages.append("➡️ Вага стабільна. Спробуй додати 1 кардіо на тиждень.")
                change_needed = True
        elif goal == "gain":
            if diff > 0.3:
                messages.append("✅ Маса набирається — чудово!")
            elif diff < 0:
                messages.append("⚠️ Вага знижується. Збільш калорійність на 150-200 ккал/день.")
                change_needed = True
            else:
                messages.append("➡️ Прогрес повільний. Додай 20 г білка на добу.")
                change_needed = True
        else:
            if abs(diff) < 0.5:
                messages.append("✅ Вага стабільна — баланс дотримано.")
            else:
                messages.append("➡️ Є коливання ваги. Перевір режим харчування.")

    if workouts_planned > 0:
        ratio = workouts_completed / workouts_planned
        if ratio >= 0.85:
            messages.append("💪 Відмінна дисципліна! Майже всі тренування виконано.")
        elif ratio >= 0.6:
            messages.append("👍 Непогано, але є пропуски. Плануй тренування у календарі.")
        else:
            messages.append("📉 Мало тренувань. Зменш к-сть до реалістичної або скоригуй розклад.")
            change_needed = True

    if avg_energy and avg_energy <= 2:
        messages.append("😴 Низький рівень енергії. Перевір сон та додай день відпочинку.")
        change_needed = True
    elif avg_energy and avg_energy >= 4:
        messages.append("⚡ Висока енергія — можна підвищити інтенсивність тренувань.")

    if not messages:
        messages.append("📊 Продовжуй дотримуватися плану. Результати прийдуть!")

    return "\n".join(messages), change_needed

# ─── АВТОРИЗАЦІЯ ТА РЕЄСТРАЦІЯ ────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    db = Session()
    if db.query(User).filter_by(email=data.get('email')).first():
        db.close()
        return jsonify({'error': 'Користувач з таким email вже існує'}), 400

    hashed_pw = generate_password_hash(data.get('password'))
    new_user = User(
        username=data.get('username'),
        email=data.get('email'),
        password_hash=hashed_pw
    )
    db.add(new_user)
    db.commit()
    session['user_id'] = new_user.id
    db.close()
    return jsonify({'success': True})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    db = Session()
    user = db.query(User).filter_by(email=data.get('email')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        session['user_id'] = user.id
        db.close()
        return jsonify({'success': True})
    db.close()
    return jsonify({'error': 'Невірний email або пароль'}), 401

@app.route("/api/profile/measurements", methods=["POST"])
def api_profile_measurements():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизовано'}), 401

    data = request.get_json()
    db = Session()

    # Зберігаємо параметри користувача
    db.add(UserMeasurement(
        user_id=session['user_id'], weight=data['weight'], height=data['height'],
        age=data['age'], gender=data['gender'], goal=data['goal'], activity_level=data['activity_level']
    ))

    # Генеруємо програму тренувань на основі параметрів
    plan_data = generate_training_plan(data['goal'], data['activity_level'])
    db.add(TrainingPlan(
        user_id=session['user_id'], goal=data['goal'],
        days_per_week=plan_data["days_per_week"],
        plan_json=json.dumps(plan_data, ensure_ascii=False)
    ))

    db.commit()
    db.close()

    # Повертаємо URL для редіректу
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    user_id = session['user_id']
    db = Session()

    if request.method == "POST":
        duration = int(request.form.get("duration", 0))
        workout_type = request.form.get("type", "")
        try:
            workout_date = datetime.strptime(request.form.get("date", ""), "%Y-%m-%d")
        except:
            workout_date = datetime.now()

        new_workout = WorkoutLog(
            user_id=user_id, date=workout_date,
            duration_minutes=duration, notes=workout_type
        )
        db.add(new_workout)
        db.commit()
        workout_id = new_workout.id
        db.close()
        return redirect(url_for("workout_feedback", workout_id=workout_id))

    # --- ОНОВЛЕНА ЛОГІКА ЗАМІРІВ ---
    last_check = db.query(BiweeklyCheck).filter_by(user_id=user_id).order_by(BiweeklyCheck.id.desc()).first()

    is_first_time = False
    if not last_check:
        # Якщо в таблиці BiweeklyCheck ще немає записів — це перший вхід
        is_first_time = True
        checkin_days = 0
    else:
        # Рахуємо дні на основі календаря (поточна дата мінус дата останнього заміру)
        days_passed = (date.today() - last_check.date).days
        if days_passed >= 14:
            checkin_days = 0 # Час робити новий замір
        else:
            checkin_days = 14 - days_passed # Скільки днів лишилось до 2 тижнів

    workouts = db.query(WorkoutLog).options(joinedload(WorkoutLog.feedback)).filter_by(user_id=user_id).order_by(WorkoutLog.id.desc()).all()
    stats = get_stats(db, user_id)

    active_plan = db.query(TrainingPlan).filter_by(user_id=user_id, is_active=True)\
                    .order_by(TrainingPlan.id.desc()).first()
    plan_data = json.loads(active_plan.plan_json) if active_plan else None

    # Передаємо is_first_time у шаблон
    rendered_html = render_template("dashboard.html", stats=stats, workouts=workouts,
                           today=datetime.now().strftime('%Y-%m-%d'),
                           checkin_days=checkin_days,
                           is_first_time=is_first_time,
                           plan_data=plan_data)

    db.close()
    return rendered_html
# ─── ВІДГУК ПІСЛЯ ТРЕНУВАННЯ ──────────────────────────────────────────────────

@app.route("/workout-feedback/<int:workout_id>", methods=["GET", "POST"])
@login_required
def workout_feedback(workout_id):
    user_id = session['user_id']
    db = Session()
    workout = db.query(WorkoutLog).filter_by(id=workout_id, user_id=user_id).first()
    if not workout:
        db.close()
        return redirect(url_for("dashboard"))

    existing_feedback = db.query(WorkoutFeedback).filter_by(workout_id=workout_id).first()

    if request.method == "POST":
        exercises = request.form.getlist("exercises")
        custom = request.form.get("custom_exercises", "").strip()
        if custom:
            exercises.append(custom)

        exercises_str = ", ".join(exercises)
        feeling_val = int(request.form.get("feeling", 3))
        energy_val = int(request.form.get("energy", 3))
        comment_str = request.form.get("comment", "").strip()

        if existing_feedback:
            existing_feedback.feeling = feeling_val
            existing_feedback.energy = energy_val
            existing_feedback.exercises_done = exercises_str
            existing_feedback.comment = comment_str
        else:
            db.add(WorkoutFeedback(
                user_id=user_id, workout_id=workout_id,
                feeling=feeling_val, energy=energy_val,
                exercises_done=exercises_str, comment=comment_str
            ))

        db.commit()
        db.close()
        flash("Дякуємо за відгук! Дані збережено.", "success")
        return redirect(url_for("dashboard"))

    if existing_feedback:
        flash("Ви вже залишили відгук для цього тренування.", "info")
        db.close()
        return redirect(url_for("dashboard"))

    workout_type = workout.notes or "default"
    exercises_list = EXERCISES_BY_TYPE.get(workout_type, EXERCISES_BY_TYPE["default"])
    rendered_html = render_template("workout_feedback.html", workout=workout, exercises_list=exercises_list)
    db.close()
    return rendered_html

# ─── КАЛЬКУЛЯТОР ──────────────────────────────────────────────────────────────

@app.route("/calculator", methods=["GET", "POST"])
@login_required
def calculator():
    user_id = session['user_id']
    if request.method == "POST":
        try:
            name   = request.form.get("name")
            weight = float(request.form.get("weight"))
            height = float(request.form.get("height"))
            age    = int(request.form.get("age"))
            gender = request.form.get("gender")
            goal   = request.form.get("goal")
            pal    = float(request.form.get("pal"))

            db = Session()
            db.add(UserMeasurement(
                user_id=user_id, weight=weight, height=height,
                age=age, gender=gender, goal=goal, activity_level=pal
            ))
            plan_data = generate_training_plan(goal, pal)
            db.query(TrainingPlan).filter_by(user_id=user_id, is_active=True)\
              .update({"is_active": False})
            db.add(TrainingPlan(
                user_id=user_id, goal=goal,
                days_per_week=plan_data["days_per_week"],
                plan_json=json.dumps(plan_data, ensure_ascii=False)
            ))
            db.commit()
            db.close()

            user = FitnessUser(name, weight, height, age, gender, goal, pal)
            return render_template("result.html", plan=user.get_full_plan(), training_plan=plan_data)

        except ValueError:
            return "Помилка! Введіть коректні числа.", 400

    return render_template("calculator.html")

# ─── ЗАМІРИ РАЗ В 2 ТИЖНІ ────────────────────────────────────────────────────

@app.route("/checkin", methods=["GET", "POST"])
@login_required
def checkin():
    user_id = session['user_id']
    db = Session()

    # Отримуємо останній замір для перевірки дати
    last_check = db.query(BiweeklyCheck).filter_by(user_id=user_id).order_by(BiweeklyCheck.id.desc()).first()

    # Визначаємо, чи пройшло 14 днів (якщо замірів немає — це перший замір, показуємо мінімум)
    show_full_form = False
    if last_check:
        days_passed = (date.today() - last_check.date).days
        if days_passed >= 14:
            show_full_form = True

    if request.method == "POST":
        try:
            new_weight = float(request.form.get("weight"))
            # Якщо полів немає у формі (міні-версія), ставимо значення за замовчуванням
            avg_energy = int(request.form.get("avg_energy", 3)) if show_full_form else 3
            completed  = int(request.form.get("workouts_completed", 0)) if show_full_form else 0
            planned    = int(request.form.get("workouts_planned", 0)) if show_full_form else 0

            waist = request.form.get("waist_cm") or None
            chest = request.form.get("chest_cm") or None
            hips  = request.form.get("hips_cm")  or None

            recommendation, change_needed = analyze_checkin(db, user_id, new_weight, completed, planned, avg_energy)

            db.add(BiweeklyCheck(
                user_id=user_id, date=date.today(),
                weight=new_weight,
                waist_cm=float(waist) if waist else None,
                chest_cm=float(chest) if chest else None,
                hips_cm=float(hips)  if hips  else None,
                avg_energy=avg_energy,
                workouts_completed=completed, workouts_planned=planned,
                recommendation=recommendation, change_needed=change_needed
            ))

            # Логіка оновлення плану залишається без змін
            db.commit()
            db.close()
            return render_template("checkin_result.html", recommendation=recommendation, change_needed=change_needed)

        except (ValueError, TypeError) as e:
            db.close()
            return f"Помилка: {e}", 400

    # Розрахунок статистики для відображення у формі (GET)
    two_weeks_ago = datetime.now() - timedelta(days=14)
    recent_workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, WorkoutLog.date >= two_weeks_ago).count()
    active_plan = db.query(TrainingPlan).filter_by(user_id=user_id, is_active=True).order_by(TrainingPlan.id.desc()).first()
    planned = (active_plan.days_per_week * 2) if active_plan else 0

    return render_template("checkin.html",
                           recent_workouts=recent_workouts,
                           planned=planned,
                           prev_check=last_check,
                           show_full_form=show_full_form)

# ─── CSV IMPORT ───────────────────────────────────────────────────────────────

@app.route("/import-csv", methods=["POST"])
@login_required
def import_csv():
    user_id = session['user_id']
    if "file" not in request.files:
        return jsonify({"error": "Файл не знайдено"}), 400
    file = request.files["file"]
    if not file.filename.endswith((".csv", ".txt")):
        return jsonify({"error": "Підтримуються лише .csv або .txt файли"}), 400

    content = file.read().decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(content[:1024], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(content), dialect=dialect)
    raw_headers = reader.fieldnames or []
    header_map = {h.strip().lower(): h for h in raw_headers}

    def find_col(*variants):
        for v in variants:
            if v in header_map:
                return header_map[v]
        return None

    col_date     = find_col("date", "дата", "day")
    col_type     = find_col("type", "тип", "activity", "sport")
    col_duration = find_col("duration", "duration_minutes", "minutes", "хвилини", "min")

    if not col_date or not col_duration:
        return jsonify({"error": f"Не знайдено колонок. Знайдені: {', '.join(raw_headers)}"}), 400

    imported, errors = 0, []
    db = Session()

    for i, row in enumerate(reader, start=2):
        try:
            raw_date = row.get(col_date, "").strip()
            raw_type = row.get(col_type, "Спорт").strip() if col_type else "Спорт"
            raw_dur  = row.get(col_duration, "").strip()
            if not raw_date or not raw_dur:
                errors.append(f"Рядок {i}: порожня дата або тривалість")
                continue
            duration = int(float(raw_dur))
            try:
                workout_date = datetime.strptime(raw_date, "%Y-%m-%d")
            except ValueError:
                workout_date = datetime.strptime(raw_date, "%d.%m.%Y")
            db.add(WorkoutLog(user_id=user_id, date=workout_date,
                              duration_minutes=duration, notes=normalize_type(raw_type)))
            imported += 1
        except Exception as e:
            errors.append(f"Рядок {i}: {str(e)}")

    db.commit()
    db.close()
    return jsonify({"imported": imported, "errors": errors[:10]})
@app.route('/stats')
@login_required
def stats():
    db = Session()
    user_id = session['user_id']

    # 1. ДАНІ ПРО ТІЛО (Вага та ІМТ)
    measurements = db.query(UserMeasurement).filter_by(user_id=user_id).all()

    if not measurements:
        db.close()
        return "<h3>У вас ще немає замірів. Спочатку заповніть дані в калькуляторі!</h3><br><a href='/calculator'>До калькулятора</a>"

    last_m = measurements[-1]

    # Захист від ZeroDivisionError
    if not last_m.height or last_m.height <= 0:
        db.close()
        return "<h3>Помилка: зріст не вказано або він дорівнює 0. Виправте це в калькуляторі!</h3><br><a href='/calculator'>До калькулятора</a>"

    labels_weight = [m.date.strftime('%d.%m') for m in measurements]
    weights_data = [m.weight for m in measurements]

    # Розрахунок ІМТ (BMI)
    height_m = last_m.height / 100
    bmi = round(last_m.weight / (height_m ** 2), 1)

    # 2. ДАНІ ПРО ТРЕНУВАННЯ (Навантаження)
    # Отримуємо останні 10 тренувань для графіка активності
    workouts = db.query(WorkoutLog).filter_by(user_id=user_id).order_by(WorkoutLog.date.asc()).all()

    labels_work = [w.date.strftime('%d.%m') for w in workouts[-10:]]
    # Розрахунок Load як на Дашборді: час * 0.3
    loads_data = [round((w.duration_minutes or 0) * 0.3, 1) for w in workouts[-10:]]

    # Логіка статусів (залишається без змін)
    if bmi < 18.5:
        status, color = "Тобі потрібно більше калорій для набору маси!", "orange"
    elif 18.5 <= bmi < 25:
        status, color = "Ти в нормі, продовжуй тренування!", "green"
    elif 25 <= bmi < 30:
        status, color = "Вага вище норми. Фокус на якість м'язів та кардіо!", "blue"
    else:
        status, color = "Показник ІМТ значний (Ожиріння). Потрібна консультація фахівця.", "red"

    db.close()
    return render_template('stats.html',
                           labels=labels_weight,
                           weights=weights_data,
                           labels_work=labels_work,
                           loads=loads_data,
                           bmi=bmi,
                           status=status,
                           color=color)
# ─── LIBRARY ─────────────────────────────────────────────────────────────────

@app.route("/library")
@login_required
def library():
    return render_template("library.html", exercises=EXERCISE_DB)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
