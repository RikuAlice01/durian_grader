import cv2

class CameraManager:
    def __init__(self, camera_ids=None):
        if camera_ids is None:
            camera_ids = [0, 1, 2, 3, 4, 5]  # ค่าเริ่มต้นกล้อง 6 ตัว
        self.camera_ids = camera_ids
        self.captures = []

    def initialize_cameras(self):
        """เชื่อมต่อกล้องทั้งหมดตาม ID"""
        self.captures = [cv2.VideoCapture(i) for i in self.camera_ids]

    def release_cameras(self):
        """ปล่อยกล้องทั้งหมดเมื่อเลิกใช้งาน"""
        for cap in self.captures:
            if cap.isOpened():
                cap.release()

    def get_frames(self):
        """ดึงภาพจากกล้องทั้งหมด"""
        frames = []
        for cap in self.captures:
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
            else:
                frames.append(None)
        return frames

    def check_status(self):
        """ตรวจสอบว่าแต่ละกล้องพร้อมใช้งานหรือไม่"""
        status = []
        for i, cap in enumerate(self.captures):
            ret, _ = cap.read()
            status.append(ret)
        return status

    def capture_single(self, index):
        """ดึงภาพจากกล้องตัวใดตัวหนึ่ง"""
        if 0 <= index < len(self.captures):
            cap = self.captures[index]
            ret, frame = cap.read()
            return frame if ret else None
        return None
