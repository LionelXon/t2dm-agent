from src.nutrition.calculator import diet_targets
from src.nutrition.exercise_target import exercise_targets
from src.schemas import PatientProfile


def main():
    cases = [
        PatientProfile(age=55, sex="male", bmi=28, weight_kg=85, height_cm=175),
        PatientProfile(
            age=68, sex="female", bmi=26, weight_kg=65, height_cm=158,
            ckd_stage="3b", egfr=35,
            complications=["周围神经病变"],
        ),
    ]
    for p in cases:
        print("=" * 40)
        print(f"患者 age={p.age} sex={p.sex} BMI={p.bmi} CKD={p.ckd_stage}")
        print("饮食目标：")
        for k, v in diet_targets(p).items():
            print(f"  {k}: {v}")
        print("运动目标：")
        for k, v in exercise_targets(p).items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()