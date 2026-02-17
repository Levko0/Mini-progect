class FitnessUser:
    def __init__(self, name, weight, height, age, gender, goal, pal=1.2):
        self.name = name
        self.weight = weight
        self.height = height
        self.age = age
        self.gender = gender.lower()  # 'male' або 'female'
        self.goal = goal.lower()      # 'loss', 'gain', 'endurance', 'maintenance'
        self.pal = pal                # Коефіцієнт активності (1.2, 1.55, 1.9)

        # Розрахункові показники
        self.bmr = 0
        self.tdee = 0
        self.tdee_adj = 0
        self.macros = {}
        self.training = {}

    def calculate_nutrition(self):
        """Розрахунок BMR, TDEE та БЖВ."""
        # 1. Основний обмін (BMR)
        if self.gender == 'male':
            self.bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            self.bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

        # 2. Добова норма (TDEE)
        self.tdee = self.bmr * self.pal

        # 3. Коригування цілі (TDEEadj)
        if self.goal == 'loss':
            self.tdee_adj = self.tdee * 0.8  # дефіцит 20%
        elif self.goal == 'gain':
            self.tdee_adj = self.tdee * 1.1  # профіцит 10%
        else:
            self.tdee_adj = self.tdee        # підтримка

        # 4. Розподіл БЖВ
        # Білки: 2.0г на 1 кг ваги
        protein_g = self.weight * 2.0
        # Жири: 0.9г на 1 кг ваги
        fat_g = self.weight * 0.9
        # Вуглеводи: решта
        carb_kcal = self.tdee_adj - (protein_g * 4) - (fat_g * 9)
        carb_g = max(0, carb_kcal / 4)

        self.macros = {
            "protein": round(protein_g, 1),
            "fat": round(fat_g, 1),
            "carbs": round(carb_g, 1)
        }

    def update_training_plan(self):
        """Призначення типу та частоти тренувань."""
        plans = {
            'loss': {"type": "Кардіо + Силові (високий темп)", "freq": "3–4 рази"},
            'gain': {"type": "Важкі силові (базові вправи)", "freq": "3 рази"},
            'endurance': {"type": "Функціональні тренування (HIIT)", "freq": "4–5 разів"}
        }
        self.training = plans.get(self.goal, {"type": "Загальна активність", "freq": "2–3 рази"})

    def get_full_plan(self):
        self.calculate_nutrition()
        self.update_training_plan()
        return {
            "user": self.name,
            "calories": round(self.tdee_adj),
            "macros": self.macros,
            "training": self.training
        }


class ProgressAnalyzer:
    @staticmethod
    def analyze(user: FitnessUser, new_weight):
        """Дерево рішень для коригування плану."""
        delta = new_weight - user.weight

        # 1. Плато (Схуднення + вага не змінилася)
        if user.goal == 'loss' and abs(delta) < 0.2:
            user.tdee_adj *= 0.95  # -5% калорій
            return "Плато! Калорії зменшено на 5%. Додайте +1 тренування."

        # 2. Втрата м'язів (Набір + вага впала)
        elif user.goal == 'gain' and delta < 0:
            user.tdee_adj *= 1.10  # +10% калорій
            return "Вага падає! Калорійність збільшена на 10%."

        # 3. Прогрес
        else:
            return "Все йде за планом! Збільште інтенсивність на 2.5–5%."





maxim = FitnessUser("Максим", 75, 180, 26, "male", "gain", 1.55)
maxim.calculate_nutrition()
# BMR = 1750, TDEE = 1750 * 1.55 = 2712.5, Gain (+10%) = 2983.75
assert round(maxim.tdee_adj) == 2984
assert maxim.macros['protein'] == 150.0

maxim.update_training_plan()
assert maxim.training['type'] == "Важкі силові (базові вправи)"

olga = FitnessUser("Ольга", 90, 170, 30, "female", "loss", 1.2)
olga.calculate_nutrition()
old_cals = olga.tdee_adj
result = ProgressAnalyzer.analyze(olga, 90)
assert olga.tdee_adj == old_cals * 0.95
assert "Плато" in result

print("Всі тести пройдено успішно! Код готовий до роботи.")
