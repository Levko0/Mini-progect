from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime, date, timedelta
from algorithm import FitnessUser
from models import (Base, engine, User, UserMeasurement, NutritionPlan,
                    WorkoutLog, WorkoutFeedback, TrainingPlan, BiweeklyCheck)
from sqlalchemy.orm import sessionmaker
import csv, io, json

app = Flask(__name__)
app.secret_key = "activetracker-secret-key"
Session = sessionmaker(bind=engine)
TEMP_USER_ID = 1

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

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_or_create_temp_user(db):
    user = db.query(User).filter_by(id=TEMP_USER_ID).first()
    if not user:
        user = User(username="default", email="default@activetracker.com", password_hash="none")
        db.add(user)
        db.commit()
    return user

def normalize_type(raw):
    if not raw:
        return "Спорт"
    return TYPE_ALIASES.get(raw.strip().lower(), raw.strip().capitalize())

def calculate_load(duration, intensity=3):
    try:
        return round(float(duration) * float(intensity) * 0.1, 1)
    except:
        return 0

def get_stats(db):
    workouts = db.query(WorkoutLog).filter_by(user_id=TEMP_USER_ID).all()
    loads = [round((w.duration_minutes or 0) * 0.3, 1) for w in workouts]
    return {
        "total": round(sum(loads), 1),
        "count": len(workouts),
        "chart_labels": [str(w.date)[:10] for w in workouts[-7:]],
        "chart_data": loads[-7:]
    }

def days_until_checkin(db):
    last = db.query(BiweeklyCheck).filter_by(user_id=TEMP_USER_ID)\
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

def analyze_checkin(db, new_weight, workouts_completed, workouts_planned, avg_energy):
    prev = db.query(BiweeklyCheck).filter_by(user_id=TEMP_USER_ID)\
             .order_by(BiweeklyCheck.id.desc()).first()
    last_m = db.query(UserMeasurement).filter_by(user_id=TEMP_USER_ID)\
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

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def dashboard():
    db = Session()
    get_or_create_temp_user(db)

    if request.method == "POST":
        duration = int(request.form.get("duration", 0))
        workout_type = request.form.get("type", "")
        try:
            workout_date = datetime.strptime(request.form.get("date", ""), "%Y-%m-%d")
        except:
            workout_date = datetime.now()

        new_workout = WorkoutLog(
            user_id=TEMP_USER_ID, date=workout_date,
            duration_minutes=duration, notes=workout_type
        )
        db.add(new_workout)
        db.commit()
        workout_id = new_workout.id
        db.close()
        return redirect(url_for("workout_feedback", workout_id=workout_id))

    workouts = db.query(WorkoutLog).filter_by(user_id=TEMP_USER_ID).order_by(WorkoutLog.id.desc()).all()
    stats = get_stats(db)
    checkin_days = days_until_checkin(db)
    active_plan = db.query(TrainingPlan).filter_by(user_id=TEMP_USER_ID, is_active=True)\
                    .order_by(TrainingPlan.id.desc()).first()
    plan_data = json.loads(active_plan.plan_json) if active_plan else None
    db.close()

    return render_template("dashboard.html", stats=stats, workouts=workouts,
                           today=datetime.now().strftime('%Y-%m-%d'),
                           checkin_days=checkin_days, plan_data=plan_data)

# ─── ВІДГУК ПІСЛЯ ТРЕНУВАННЯ ──────────────────────────────────────────────────

@app.route("/workout-feedback/<int:workout_id>", methods=["GET", "POST"])
def workout_feedback(workout_id):
    db = Session()
    workout = db.query(WorkoutLog).filter_by(id=workout_id, user_id=TEMP_USER_ID).first()
    if not workout:
        db.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        exercises = request.form.getlist("exercises")
        custom = request.form.get("custom_exercises", "").strip()
        if custom:
            exercises.append(custom)

        db.add(WorkoutFeedback(
            user_id=TEMP_USER_ID, workout_id=workout_id,
            feeling=int(request.form.get("feeling", 3)),
            energy=int(request.form.get("energy", 3)),
            exercises_done=", ".join(exercises),
            comment=request.form.get("comment", "").strip()
        ))
        db.commit()
        db.close()
        flash("Дякуємо за відгук! Дані збережено.", "success")
        return redirect(url_for("dashboard"))

    workout_type = workout.notes or "default"
    exercises_list = EXERCISES_BY_TYPE.get(workout_type, EXERCISES_BY_TYPE["default"])
    db.close()
    return render_template("workout_feedback.html", workout=workout, exercises_list=exercises_list)

# ─── КАЛЬКУЛЯТОР ──────────────────────────────────────────────────────────────

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
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
            get_or_create_temp_user(db)
            db.add(UserMeasurement(
                user_id=TEMP_USER_ID, weight=weight, height=height,
                age=age, gender=gender, goal=goal, activity_level=pal
            ))
            plan_data = generate_training_plan(goal, pal)
            db.query(TrainingPlan).filter_by(user_id=TEMP_USER_ID, is_active=True)\
              .update({"is_active": False})
            db.add(TrainingPlan(
                user_id=TEMP_USER_ID, goal=goal,
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
def checkin():
    db = Session()
    get_or_create_temp_user(db)

    if request.method == "POST":
        try:
            new_weight = float(request.form.get("weight"))
            avg_energy = int(request.form.get("avg_energy", 3))
            completed  = int(request.form.get("workouts_completed", 0))
            planned    = int(request.form.get("workouts_planned", 0))
            waist = request.form.get("waist_cm") or None
            chest = request.form.get("chest_cm") or None
            hips  = request.form.get("hips_cm")  or None

            recommendation, change_needed = analyze_checkin(db, new_weight, completed, planned, avg_energy)

            db.add(BiweeklyCheck(
                user_id=TEMP_USER_ID, date=date.today(),
                weight=new_weight,
                waist_cm=float(waist) if waist else None,
                chest_cm=float(chest) if chest else None,
                hips_cm=float(hips)  if hips  else None,
                avg_energy=avg_energy,
                workouts_completed=completed, workouts_planned=planned,
                recommendation=recommendation, change_needed=change_needed
            ))

            if change_needed:
                last_m = db.query(UserMeasurement).filter_by(user_id=TEMP_USER_ID)\
                           .order_by(UserMeasurement.id.desc()).first()
                if last_m:
                    new_plan = generate_training_plan(last_m.goal, last_m.activity_level)
                    db.query(TrainingPlan).filter_by(user_id=TEMP_USER_ID, is_active=True)\
                      .update({"is_active": False})
                    db.add(TrainingPlan(
                        user_id=TEMP_USER_ID, goal=last_m.goal,
                        days_per_week=new_plan["days_per_week"],
                        plan_json=json.dumps(new_plan, ensure_ascii=False)
                    ))

            db.commit()
            db.close()
            return render_template("checkin_result.html",
                                   recommendation=recommendation, change_needed=change_needed)

        except (ValueError, TypeError) as e:
            db.close()
            return f"Помилка: {e}", 400

    two_weeks_ago = datetime.now() - timedelta(days=14)
    recent_workouts = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == TEMP_USER_ID,
        WorkoutLog.date >= two_weeks_ago
    ).count()
    active_plan = db.query(TrainingPlan).filter_by(user_id=TEMP_USER_ID, is_active=True)\
                    .order_by(TrainingPlan.id.desc()).first()
    planned = (active_plan.days_per_week * 2) if active_plan else 0
    prev_check = db.query(BiweeklyCheck).filter_by(user_id=TEMP_USER_ID)\
                   .order_by(BiweeklyCheck.id.desc()).first()
    db.close()

    return render_template("checkin.html", recent_workouts=recent_workouts,
                           planned=planned, prev_check=prev_check)

# ─── CSV IMPORT ───────────────────────────────────────────────────────────────

@app.route("/import-csv", methods=["POST"])
def import_csv():
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
    get_or_create_temp_user(db)

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
            db.add(WorkoutLog(user_id=TEMP_USER_ID, date=workout_date,
                              duration_minutes=duration, notes=normalize_type(raw_type)))
            imported += 1
        except Exception as e:
            errors.append(f"Рядок {i}: {str(e)}")

    db.commit()
    db.close()
    return jsonify({"imported": imported, "errors": errors[:10]})

# ─── LIBRARY ─────────────────────────────────────────────────────────────────

@app.route("/library")
def library():
    return render_template("library.html", exercises=EXERCISE_DB)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
