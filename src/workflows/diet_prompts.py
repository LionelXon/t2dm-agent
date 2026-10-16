from src.nutrition.food_db import FOOD_DB

DIET_SYSTEM_PROMPT = """你是一名2型糖尿病营养师。
你只能从【可用食物列表】里选食物，不允许发明新食物。
你只能输出"食物名称 + 克重"，绝对不要写任何营养数字（kcal、蛋白、碳水、脂肪、盐、纤维都不要写）。

严格输出 JSON：
{
  "answer": "对这份餐单的简要说明",
  "citations": [
    {"chunk_id": "片段ID", "quote": "从片段中逐字复制的句子"}
  ],
  "meal_plan": {
    "meals": [
      {"name": "早餐", "items": [{"food": "燕麦", "grams": 60}, ...]},
      {"name": "午餐", "items": [...]},
      {"name": "晚餐", "items": [...]}
    ]
  }
}

规则：
1. 只能使用【可用食物列表】中的食物名称，必须完全一致。
2. 一天的餐单要尽量接近给定能量目标与宏量区间。
3. 不要输出 JSON 之外的任何文字。
"""

def build_diet_user_prompt(
    patient_summary: str,
    targets: dict,
    chunks,
) -> str:
    food_list = "、".join(sorted(FOOD_DB.keys()))

    kcal = targets["energy"]["energy_target_kcal"]
    carb_lo, carb_hi = targets["macros"]["carb_ratio_range"]
    fat_lo, fat_hi = targets["macros"]["fat_ratio_range"]
    pro_lo, pro_hi = targets["protein"]["protein_g_range"]

    carb_g_lo = round(kcal * carb_lo / 4)
    carb_g_hi = round(kcal * carb_hi / 4)
    fat_g_lo = round(kcal * fat_lo / 9)
    fat_g_hi = round(kcal * fat_hi / 9)

    lines = [
        "【患者摘要】",
        patient_summary,
        "",
        "【全天营养目标（务必达到）】",
        f"- 能量：{kcal} kcal（允许 ±10%）",
        f"- 碳水化合物：约 {carb_g_lo}-{carb_g_hi} g",
        f"- 蛋白质：约 {pro_lo}-{pro_hi} g",
        f"- 脂肪：约 {fat_g_lo}-{fat_g_hi} g",
        f"- 食盐：< {targets['macros']['salt_g_per_day_max']} g/d",
        "",
        "【配餐结构要求】",
        "- 必须输出 3 餐（早/午/晚）",
        "- 每餐必须包含：主食 1 种、蛋白类 1-2 种、蔬菜 1-2 种",
        "- 早餐另加乳制品 1 种",
        "- 全天至少出现 1 种水果、1 种坚果",
        "- 全天油脂（橄榄油）合计不超过 25g",
        "- 全天食盐用量写 0g（由代码忽略）",
        "",
        "【宏量比例要求（务必满足）】",
        f"- 碳水供能比 {carb_lo:.0%}-{carb_hi:.0%}：主食别过多也别过少",
        f"- 脂肪供能比 {fat_lo:.0%}-{fat_hi:.0%}：控制坚果和油脂总量",
        f"- 蛋白质 {pro_lo}-{pro_hi} g：肉蛋奶豆类别超量",
        "",
        "【可用食物列表】",
        food_list,
        "",
        "【指南片段】",
    ]
    for c in chunks:
        lines.append(f"[chunk_id={c.chunk_id} | rec_id={c.rec_id} | {c.section}]")
        lines.append(c.text)
        lines.append("")
    return "\n".join(lines)

def build_diet_rewrite_prompt(violations, nutrition=None, targets=None) -> str:
    lines = ["你上一次的餐单违反了以下硬规则："]
    for v in violations:
        lines.append(f"- [{v.severity}] {v.rule_id}: {v.message}（依据：{v.evidence}）")

    if nutrition and targets:
        total = nutrition.get("total", {})
        kcal_t = targets["energy"]["energy_target_kcal"]
        pro_lo, pro_hi = targets["protein"]["protein_g_range"]
        lines.append("")
        lines.append("【上一次实际值 vs 目标】")
        lines.append("【调整优先级】")
        lines.append("1. 能量偏差优先用主食克重调整（±30g 主食约 ±100 kcal）")
        lines.append("2. 蛋白超标时，先减肉蛋鱼类克重，别动蔬菜")
        lines.append("3. 碳水偏低时加主食，脂肪偏高时减坚果和油脂")
        lines.append("4. 每次调整幅度 10-20%，不要大改")
        lines.append(f"- 能量：{total.get('kcal')} kcal（目标 {kcal_t}）")
        lines.append(f"- 蛋白质：{total.get('protein_g')} g（目标 {pro_lo}-{pro_hi} g）")
        lines.append(f"- 碳水供能比：{total.get('carb_ratio')}（目标 {targets['macros']['carb_ratio_range']}）")
        lines.append(f"- 脂肪供能比：{total.get('fat_ratio')}（目标 {targets['macros']['fat_ratio_range']}）")
        lines.append("")
        lines.append("请按差值调整克重：能量偏低就整体加量，蛋白偏低就加蛋白类食物。")
        lines.append("")
        lines.append("严格按这些约束重新生成餐单，仍然输出相同 JSON 结构。")
    return "\n".join(lines)