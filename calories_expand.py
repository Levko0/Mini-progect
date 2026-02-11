def get_full_fitness_recommendation(weight, height, age, gender, goal, activity_level=1.2):
    # 1. Розрахунок BMR (Основний обмін)
    if gender.lower() == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    # 2. Розрахунок TDEE (Загальні витрати)
    tdee = bmr * activity_level

    # 3. Цільова норма калорій та параметри тренувань
    recommendations = {}

    if goal == 'loss':
        tdee_adj = tdee * 0.8  # Дефіцит 20%
        recommendations = {
            "тип_тренувань": "Кардіо + Силові (високий темп)",
            "частота": "3–4 рази на тиждень",
            "опис_цілі": "Схуднення"
        }
    elif goal == 'gain':
        tdee_adj = tdee * 1.1  # Профіцит 10%
        recommendations = {
            "тип_тренувань": "Важкі силові (базові вправи)",
            "частота": "3 рази на тиждень",
            "опис_цілі": "Набір маси"
        }
    elif goal == 'endurance':
        tdee_adj = tdee  # Для витривалості зазвичай тримаємо баланс або невеликий плюс
        recommendations = {
            "тип_тренувань": "Функціональні тренування (HIIT)",
            "частота": "4–5 разів на тиждень",
            "опис_цілі": "Розвиток витривалості"
        }
    else:
        tdee_adj = tdee
        recommendations = {
            "тип_тренувань": "Загальна активність / Підтримка",
            "частота": "2–3 рази на тиждень",
            "опис_цілі": "Підтримка форми"
        }

    # 4. Розрахунок БЖВ
    # Використовуємо середні значення: Білки 2г/кг, Жири 0.9г/кг
    proteins_g = weight * 2.0
    fats_g = weight * 0.9

    # Вуглеводи (залишок)
    proteins_kcal = proteins_g * 4
    fats_kcal = fats_g * 9
    carbs_kcal = tdee_adj - proteins_kcal - fats_kcal
    carbs_g = max(0, carbs_kcal / 4)

    return {
        "user_metrics": {
            "bmr": round(bmr),
            "tdee": round(tdee),
            "target_calories": round(tdee_adj)
        },
        "macros": {
            "proteins": round(proteins_g),
            "fats": round(fats_g),
            "carbs": round(carbs_g)
        },
        "training": recommendations
    }

