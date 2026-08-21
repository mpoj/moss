import json

OUTPUT_FILENAME = "teamsX.json"
teams_data = []

# --- กำหนดค่าเริ่มต้น ---
BASE_STUDENT_ID = 68070501201  # เริ่มต้นที่เลขนี้ตามตัวอย่าง JSON
START_TEAM_ID = 1201
NUM_TO_CREATE = 2

# --- ค่าคงที่ ---
GROUP_ID = "13"       # เปลี่ยนเป็น String ตาม JSONฏ
ORG_ID = "INST-1"     # เปลี่ยนเป็น String ตาม JSON

print(f"กำลังสร้าง {NUM_TO_CREATE} ทีม...")

# --- วนลูปสร้างข้อมูล ---
for i in range(NUM_TO_CREATE):
    
    # คำนวณค่า ID ต่างๆ (บวกเพิ่มตามลำดับ i)
    current_val = BASE_STUDENT_ID + i
    current_team_id = str(START_TEAM_ID + i)
    current_full_id_str = str(current_val)

    # สร้าง Object ตามโครงสร้างที่ต้องการ
    team_object = {
        "id": current_team_id,
        "icpc_id": current_team_id,
        "label": current_full_id_str,
        "group_ids": [GROUP_ID],
        "name": current_team_id,
        "display_name": f"{current_team_id}_SECA",
        "organization_id": [ORG_ID],
        "location": {
            "description": current_full_id_str
        }
    }
    
    teams_data.append(team_object)

# --- บันทึกไฟล์ JSON ---
try:
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(teams_data, f, indent=2, ensure_ascii=False)
    print(f"✅ สร้างไฟล์ {OUTPUT_FILENAME} สำเร็จ (มี {len(teams_data)} ทีม)")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดในการบันทึกไฟล์: {e}")
