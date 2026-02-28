from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from algorithm import FitnessUser
from models import Session, Workout, UserProfile
import csv, io

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

# Відповідність назв типів тренувань (для підтримки різних трекерів)
TYPE_ALIASES = {
    "run": "Біг", "running": "Біг", "біг": "Біг", "бег": "Біг",
    "gym": "Зал", "strength": "Зал", "зал": "Зал", "силове": "Зал", "weightlifting": "Зал",
    "sport": "Спорт", "спорт": "Спорт", "game": "Спорт",
    "cycling": "Велосипед", "bike": "Велосипед", "велосипед": "Велосипед",
    "swimming": "Спорт", "swim": "Спорт", "плавання": "Спорт",
    "walking": "Біг", "walk": "Біг", "ходьба": "Біг",
}

def normalize_type(raw):
    """Нормалізує назву типу тренування з будь-якого трекера."""
    if not raw:
        return "Спорт"
    return TYPE_ALIASES.get(raw.strip().lower(), raw.strip().capitalize())

def get_stats(db_session):
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
        return round(float(duration) * float(intensity) * 0.1, 1)
    except:
        return 0

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def dashboard():
    db = Session()
    if request.method == "POST":
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

    workouts = db.query(Workout).order_by(Workout.id.desc()).all()
    stats = get_stats(db)
    db.close()
    return render_template("dashboard.html", stats=stats, workouts=workouts, today=datetime.now().strftime('%Y-%m-%d'))

# ─── CSV IMPORT ───────────────────────────────────────────────────────────────

@app.route("/import-csv", methods=["POST"])
def import_csv():
    """
    Приймає CSV файл і зберігає тренування в базу даних.

    Підтримує колонки (будь-який порядок, автодетектування):
      - date / дата / day
      - type / тип / activity / sport
      - duration / minutes / хвилини / час / min
      - intensity / інтенсивність / level  (необов'язково, default=3)

    Повертає JSON: { imported: N, errors: [...] }
    """
    if "file" not in request.files:
        return jsonify({"error": "Файл не знайдено"}), 400

    file = request.files["file"]
    if not file.filename.endswith((".csv", ".txt")):
        return jsonify({"error": "Підтримуються лише .csv або .txt файли"}), 400

    content = file.read().decode("utf-8-sig", errors="replace")  # utf-8-sig знімає BOM

    # Автодетектування роздільника
    dialect = csv.Sniffer().sniff(content[:1024], delimiters=",;\t")
    reader = csv.DictReader(io.StringIO(content), dialect=dialect)

    # Нормалізуємо заголовки (lowercase, trim)
    raw_headers = reader.fieldnames or []
    header_map = {h.strip().lower(): h for h in raw_headers}

    def find_col(*variants):
        """Знаходить колонку за можливими варіантами назви."""
        for v in variants:
            if v in header_map:
                return header_map[v]
        return None

    col_date      = find_col("date", "дата", "day", "д")
    col_type      = find_col("type", "тип", "activity", "sport", "активність", "вид")
    col_duration  = find_col("duration", "duration_minutes", "minutes", "хвилини", "час", "min", "тривалість")
    col_intensity = find_col("intensity", "інтенсивність", "level", "рівень", "effort")

    if not col_date or not col_duration:
        return jsonify({
            "error": "Не знайдено обов'язкових колонок (date, duration). "
                     f"Знайдені колонки: {', '.join(raw_headers)}"
        }), 400

    imported = 0
    errors = []
    db = Session()

    for i, row in enumerate(reader, start=2):  # рядок 1 = заголовок
        try:
            raw_date     = row.get(col_date, "").strip()
            raw_type     = row.get(col_type, "Спорт").strip() if col_type else "Спорт"
            raw_duration = row.get(col_duration, "").strip()
            raw_intensity = row.get(col_intensity, "3").strip() if col_intensity else "3"

            if not raw_date or not raw_duration:
                errors.append(f"Рядок {i}: порожня дата або тривалість — пропущено")
                continue

            duration  = float(raw_duration)
            intensity = max(1.0, min(5.0, float(raw_intensity) if raw_intensity else 3.0))
            workout_type = normalize_type(raw_type)
            load = calculate_load(duration, intensity)

            db.add(Workout(
                date=raw_date,
                type=workout_type,
                duration=int(duration),
                load=load
            ))
            imported += 1

        except Exception as e:
            errors.append(f"Рядок {i}: {str(e)}")

    db.commit()
    db.close()

    return jsonify({
        "imported": imported,
        "errors": errors[:10]  # максимум 10 помилок у відповіді
    })

# ─── CALCULATOR ───────────────────────────────────────────────────────────────

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

# ─── LIBRARY ─────────────────────────────────────────────────────────────────

@app.route("/library")
def library():
    return render_template("library.html", exercises=EXERCISE_DB)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
