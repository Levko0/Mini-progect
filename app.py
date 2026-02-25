from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from algotitm import FitnessUser 
from models import Session, Workout, UserProfile # Підключаємо базу даних

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)