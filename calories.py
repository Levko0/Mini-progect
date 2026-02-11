def calculate_fitness_plan(weight, height, age, gender, goal, activity_level=1.2):
    """
    Розраховує норму калорій залежно від параметрів та спортивної цілі.

    :param goal: 'loss' (схуднення), 'gain' (набір), 'maintenance' (підтримка)
    """

    # 1. Розрахунок базового обміну (BMR)
    if gender.lower() == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    # 2. Розрахунок добових витрат (TDEE)
    tdee = bmr * activity_level

    # 3. Коригування під ціль користувача
    if goal == 'loss':
        final_calories = tdee * 0.85  # Дефіцит 15%
        description = "Для схуднення"
    elif goal == 'gain':
        final_calories = tdee * 1.10  # Профіцит 10%
        description = "Для набору маси"
    else:
        final_calories = tdee
        description = "Для підтримки ваги"

    return {
        "базовий_метаболізм_bmr": round(bmr),
        "добова_норма_tdee": round(tdee),
        "рекомендовано_споживати": round(final_calories),
        "мета": description
    }


print(calculate_fitness_plan(78, 184, 17, "male", 'gain'))
