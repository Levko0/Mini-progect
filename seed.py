from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Exercise

# 1. Підключаємось до бази даних
engine = create_engine('sqlite:///fitness_app.db')
Session = sessionmaker(bind=engine)
session = Session()

if session.query(Exercise).count() == 0:
    print("Завантажуємо тренувальну програму з розподілом по днях (УКР/ЕНГ відео)...")

    exercises_data = [
        # ==========================================
        # ДЕНЬ 1
        # ==========================================
        Exercise(name="Віджимання на брусах", category="base_fullbody", is_essential=True, day_number=1,
                 difficulty="medium", description="Темп 3111. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=2z8JmcrW-As"),
        Exercise(name="Тяга верхнього блоку / Підтягування", category="base_fullbody", is_essential=True, day_number=1,
                 difficulty="medium", description="Темп 3111. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=nelSwzGokpA"),
        Exercise(name="Розгинання ніг", category="base_fullbody", is_essential=False, day_number=1,
                 difficulty="easy", description="Темп 3111. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=m0FOpMEgero"),
        Exercise(name="Махи з гантелями", category="base_fullbody", is_essential=False, day_number=1,
                 difficulty="easy", description="Темп 2111. 2 підходи по 8-12 повторень.", video_url="https://www.youtube.com/watch?v=3VcKaXpzqRo"),
        Exercise(name="Згинання ніг сидячи", category="base_fullbody", is_essential=False, day_number=1,
                 difficulty="easy", description="Темп 3112. 2 підходи по 10 повторень.", video_url="https://www.youtube.com/watch?v=F488k67BTNo"),
        Exercise(name="Скручування для пресу", category="base_fullbody", is_essential=False, day_number=1,
                 difficulty="easy", description="Темп 3111. 2 підходи по 15-20 повторень.", video_url="https://www.youtube.com/watch?v=MKmoRw5OzYg"),

        # ==========================================
        # ДЕНЬ 2
        # ==========================================
        Exercise(name="Жим гантелей під кутом", category="base_fullbody", is_essential=True, day_number=2,
                 difficulty="medium", description="Темп 3111. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=8iPEnn-ltC8"),
        Exercise(name="Тяга сидячи у хамері", category="base_fullbody", is_essential=True, day_number=2,
                 difficulty="medium", description="Темп 3111. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=GZbfZ033f74"),
        Exercise(name="Румунська тяга", category="base_fullbody", is_essential=True, day_number=2,
                 difficulty="hard", description="Темп 3111. 1-2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=amSyUxzkJnQ"),
        Exercise(name="Згинання на біцепс", category="base_fullbody", is_essential=False, day_number=2,
                 difficulty="easy", description="Темп 3111. 2 підходи по 6-9 повторень.", video_url="https://www.youtube.com/watch?v=in7PaeYlhrM"),
        Exercise(name="Розгинання для триголового", category="base_fullbody", is_essential=False, day_number=2,
                 difficulty="easy", description="Темп 3111. 2 підходи по 6-9 повторень.", video_url="https://www.youtube.com/watch?v=nRiJVZDpdL0"),
        Exercise(name="Жим носками (ікри)", category="base_fullbody", is_essential=False, day_number=2,
                 difficulty="easy", description="Темп 2411. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=-M4-G8p8fmc"),

        # ==========================================
        # ДЕНЬ 3
        # ==========================================
        Exercise(name="Тяга 1 рукою", category="base_fullbody", is_essential=True, day_number=3,
                 difficulty="medium", description="Темп 3111. 1-2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=pYcpY20QaE8"),
        Exercise(name="Жим ногами", category="base_fullbody", is_essential=True, day_number=3,
                 difficulty="hard", description="Темп 3111. 2 підходи по 6-8 повторень.", video_url="https://www.youtube.com/watch?v=IZxyjW7OSvc"),
        Exercise(name="Метелик для грудних", category="base_fullbody", is_essential=False, day_number=3,
                 difficulty="easy", description="Темп 3111. 2 підходи по 8-10 повторень.", video_url="https://www.youtube.com/watch?v=eGjt4joGQ_c"),
        Exercise(name="Тяга для верху спини", category="base_fullbody", is_essential=False, day_number=3,
                 difficulty="medium", description="Темп 3111. 2 підходи по 7-9 повторень.", video_url="https://www.youtube.com/watch?v=xdW8qS4iL54"),
        Exercise(name="Молотки", category="base_fullbody", is_essential=False, day_number=3,
                 difficulty="easy", description="Темп 3111. 2 підходи по 7-9 повторень.", video_url="https://www.youtube.com/watch?v=zC3nLlEvin4"),

        # ==========================================
        # СПОРТИВНІ МОДУЛІ (Без прив'язки до дня)
        # ==========================================
        # Футболісти
        Exercise(name="Болгарські випади", category="football", is_essential=False, day_number=None,
                 difficulty="hard", description="Розвиток сили та балансу для футболістів.", video_url="https://www.youtube.com/watch?v=WVHeO0JYW5I"),
        Exercise(name="Нордичні згинання", category="football", is_essential=False, day_number=None,
                 difficulty="hard", description="Ексцентричне зміцнення біцепса стегна для гальмування.", video_url="https://www.youtube.com/watch?v=63FvI4dXn2M"),
        
        # Армреслери
        Exercise(name="Згинання зап'ястя", category="armwrestling", is_essential=False, day_number=None,
                 difficulty="medium", description="Зміцнення кисті для армреслерів.", video_url="https://www.youtube.com/watch?v=RcOiv-ABgqM"),
        
        # Волейболісти
        Exercise(name="Стрибки на тумбу", category="volleyball", is_essential=False, day_number=None,
                 difficulty="medium", description="Вибухова сила для волейболістів.", video_url="https://www.youtube.com/watch?v=PTqVObCxIt8"),
        Exercise(name="Поштовховий швунг штанги", category="volleyball", is_essential=False, day_number=None,
                 difficulty="hard", description="Синхронізація ніг та плечей для потужного викиду рук.", video_url="https://www.youtube.com/watch?v=VFNktIvMDN8"),

        # Боксери
        Exercise(name="Обертання Landmine", category="boxing", is_essential=False, day_number=None,
                 difficulty="medium", description="Ротаційна сила удару для боксерів.", video_url="https://www.youtube.com/watch?v=wpfYRQGYVm4"),

        # Борці
        Exercise(name="Присідання Зерчера", category="wrestling", is_essential=False, day_number=None,
                 difficulty="hard", description="Імітація утримання суперника.", video_url="https://www.youtube.com/watch?v=9MSIP2LtMFI"),
        Exercise(name="Тяга Пендлі", category="wrestling", is_essential=False, day_number=None,
                 difficulty="hard", description="Строга тяга штанги з підлоги без інерції.", video_url="https://www.youtube.com/watch?v=Uy17rdP6G14")
    ]

    session.add_all(exercises_data)
    session.commit()
    print(f"Успішно додано {len(exercises_data)} вправ (УКР/ЕНГ)!")
else:
    print("База вже містить дані. Якщо хочете оновити відео — видаліть файл fitness_app.db та запустіть скрипт знову.")

session.close()
