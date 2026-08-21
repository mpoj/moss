import json
import random
import string

OUTPUT_FILENAME = "ACCOUNT.json"
LOG_FILENAME = "passwords_list.txt"  # ไฟล์สำหรับเก็บรายชื่อไว้ดู
accounts_data = []

# --- กำหนดค่าเริ่มต้น ---
BASE_STUDENT_FULL_ID = 68070501201
START_TEAM_ID = 152  
NUM_TO_CREATE = 2    # ลองสร้างสัก 5 บัญชี
PASSWORD_LENGTH = 8 

def generate_random_password(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

print(f"{'Username':<15} | {'Password':<10} | {'Team ID':<8}")
print("-" * 40)

# สำหรับเก็บข้อความที่จะเขียนลงไฟล์ txt
log_lines = []

for i in range(NUM_TO_CREATE):
    current_full_id = str(BASE_STUDENT_FULL_ID + i)
    current_team_id = str(START_TEAM_ID + i) 
    random_password = generate_random_password(PASSWORD_LENGTH)

    # แสดงผลบนหน้าจอทันที
    print(f"{current_full_id:<15} | {random_password:<10} | {current_team_id:<8}")

    # เก็บข้อมูลไว้สำหรับไฟล์ log (.txt)
    log_lines.append(f"User: {current_full_id} | Pass: {random_password} | Team: {current_team_id}\n")

    account_object = {
        "id": current_full_id,                 
        "username": current_full_id,           
        "name": "",  
        "type": "team",                        
        "team_id": current_team_id, 
        "password": random_password
    }
    accounts_data.append(account_object)

# --- บันทึกไฟล์ JSON ---
with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
    json.dump(accounts_data, f, indent=2, ensure_ascii=False)

# --- บันทึกไฟล์ TXT (เอาไว้ดูรหัสผ่านแยกต่างหาก) ---
with open(LOG_FILENAME, 'w', encoding='utf-8') as f:
    f.writelines(log_lines)

print("-" * 40)
print(f"✅ บันทึก JSON เรียบร้อยในไฟล์: {OUTPUT_FILENAME}")
print(f"📄 ดูรหัสผ่านทั้งหมดได้ที่ไฟล์: {LOG_FILENAME}")