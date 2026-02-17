from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from algotitm import FitnessUser 

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
        {"name": "Футбол", "desc": "Активна гра.", "img": NEW_IMAGE_URL}
    ]
}

workouts = []

def calculate_load(duration, intensity):
    if not duration or not intensity: return 0
    return int(duration) * int(intensity)

def get_stats():
    today = datetime.now().date()
    week_ago = today - timedelta(days=6)
    
    labels = []
    data = []
    
    for i in range(7):
        day = week_ago + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        labels.append(day.strftime('%d.%m'))
        
        day_load = sum(w['load'] for w in workouts if w['date'] == day_str)
        data.append(day_load)

    return {
        "total": sum(w['load'] for w in workouts),
        "count": len(workouts),
        "chart_labels": labels,
        "chart_data": data
    }

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        workouts.append({
            "date": request.form.get("date"),
            "type": request.form.get("type"),
            "duration": request.form.get("duration"),
            "load": calculate_load(request.form.get("duration"), request.form.get("intensity"))
        })
        return redirect(url_for("dashboard"))
    
    return render_template("dashboard.html", stats=get_stats(), workouts=workouts, today=datetime.now().strftime('%Y-%m-%d'))

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

            user = FitnessUser(name, weight, height, age, gender, goal, pal)
            return render_template("result.html", plan=user.get_full_plan())

        except ValueError:
            return "Помилка! Введіть коректні числа.", 400

    return render_template("calculator.html")

@app.route("/library")
def library():
    return render_template("library.html", exercises=EXERCISE_DB)

if __name__ == "__main__":
    app.run(debug=True)