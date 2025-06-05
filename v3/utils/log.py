import os
import traceback

# เพิ่มฟังก์ชันสำหรับบันทึกข้อผิดพลาด
def log_error(error_message):
    """บันทึกข้อผิดพลาดลงในไฟล์ logs/DDMMYYYY-hhmm.txt"""
    log_dir = "../logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    current_time = datetime.now().strftime("%d%m%Y-%H%M")
    log_file_path = os.path.join(log_dir, f"{current_time}.txt")
    
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]\n")
        log_file.write(error_message + "\n")
        log_file.write("-" * 50 + "\n")
