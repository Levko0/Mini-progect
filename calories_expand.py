def calculate_detailed_plan(weight, height, age, gender, goal, activity_level=1.2):
    if gender.lower() == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    # 2. Загальні витрати (TDEE)
    tdee = bmr * activity_level

    # 3. Коригування під ціль (TDEEadj)
    if goal == 'loss':
        tdee_adj = tdee * 0.8  # Дефіцит 20%
    elif goal == 'gain':
        tdee_adj = tdee * 1.1  # Профіцит 10%
    else:
        tdee_adj = tdee        # Підтримка

    proteins_g = weight * 2.0
    proteins_kcal = proteins_g * 4

    fats_g = weight * 0.9
    fats_kcal = fats_g * 9

    carbs_kcal = tdee_adj - proteins_kcal - fats_kcal
    carbs_g = carbs_kcal / 4

    # Якщо вуглеводів виходить замало (критичний випадок), ставимо мінімум 0
    carbs_g = max(0, carbs_g)

    return {
        "ціль": goal,
        "денна_калорійність": round(tdee_adj),
        "білки_г": round(proteins_g),
        "жири_г": round(fats_g),
        "вуглеводи_г": round(carbs_g),
        "розподіл_енергії": {
            "білки_ккал": round(proteins_kcal),
            "жири_ккал": round(fats_kcal),
            "вуглеводи_ккал": round(carbs_kcal)
        }
    }

