from src.schemas import PatientProfile, GuidelineChunk
def test_patient_profile():
    p = PatientProfile(age=68, bmi=27.5, egfr=28)
    assert p.age == 68
    assert p.health_status == "good"
    
def test_guideline_chunk():
    c = GuidelineChunk(
        chunk_id="cn_t2dm_2020_rec_5_1_2",
        guide_name="中国T2DM防治指南",
        year=2020,
        section="综合控制目标",
        rec_id="5.1.2",
        text="一般成人 HbA1c 目标 <7.0%"
    )
    assert c.rec_id == "5.1.2"