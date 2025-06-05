import customtkinter as ctk
from customtkinter import CTkImage, CTkFont
import tkinterdnd2
from tkinterdnd2 import DND_FILES
from tkinter import filedialog
import cv2
from PIL import Image, ImageOps, ImageFilter
import numpy as np
import os
import threading
import time
from datetime import datetime

from utils.config_loader import load_config, save_config
from utils.durian_grader import process_image

# ตั้งค่าธีมสีและรูปแบบ
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

class DurianGraderApp(tkinterdnd2.TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        # Create a CustomTkinter frame as main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill='both', expand=True)

        # ตั้งค่าหน้าต่างหลัก
        self.title("Durian Grading System")
        self.geometry("1400x900")
        self.minsize(1000, 800)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0)
        self.main_container.grid_rowconfigure(1, weight=0)
        self.main_container.grid_rowconfigure(2, weight=1)

        # ตัวแปรเก็บข้อมูล
        self.image_path = None
        self.original_image = None
        self.result_history = []
        self.is_analyzing = False
        
        # ตัวแปรสำหรับกล้อง
        self.camera = None
        self.camera_active = False
        self.camera_thread = None
        self.fps = 24
        self.frame_interval = 1.0 / self.fps
        self.last_analysis_time = 0
        self.analysis_interval = 1.0  # วิเคราะห์ทุก 1 วินาที
        self.available_cameras = []
        self.selected_camera_idx = 0
        
        # ตัวแปรสำหรับการกำหนดค่า content frame
        self.content_columns = 2  # จำนวนคอลัมน์ที่สามารถกำหนดได้
        self.show_result_panel = True  # แสดงแผงผลลัพธ์หรือไม่

        # กำหนดสีและฟอนต์
        self.primary_color = "#4CAF50"
        self.secondary_color = "#689F38"
        self.header_font = CTkFont(family="Helvetica", size=28, weight="bold")
        self.button_font = CTkFont(family="Helvetica", size=14, weight="bold")
        self.text_font = CTkFont(family="Helvetica", size=13)
        self.result_font = CTkFont(family="Consolas", size=14)
        
        # ตรวจหากล้องที่มีอยู่
        self._detect_cameras()
        
        # สร้าง UI
        self._create_header_frame()
        self._create_button_frame()
        self._create_content_frame()
        
        # สร้างแถบสถานะ
        self.status_var = ctk.StringVar(value="พร้อมใช้งาน")
        self.status_bar = ctk.CTkLabel(
            self.main_container, 
            textvariable=self.status_var, 
            font=("Helvetica", 12),
            height=25
        )
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))

    def _detect_cameras(self):
        """ตรวจหากล้องที่มีใช้ได้ในระบบ"""
        self.available_cameras = []
        
        # ตรวจสอบกล้องสูงสุด 10 ตัว
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.available_cameras.append(i)
                cap.release()
            else:
                break
        
        if not self.available_cameras:
            print("ไม่พบกล้องในระบบ")

    def configure_content_frame(self, columns=2, show_result_panel=True):
        """กำหนดค่าการแสดงผลของ content frame"""
        self.content_columns = columns
        self.show_result_panel = show_result_panel
        # รีเฟรช content frame
        self._recreate_content_frame()

    def _recreate_content_frame(self):
        """สร้าง content frame ใหม่ตามการกำหนดค่า"""
        if hasattr(self, 'content_frame'):
            self.content_frame.destroy()
        self._create_content_frame()

    def _create_header_frame(self):
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color=self.primary_color, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🍈 AI Durian Grading System", 
            font=self.header_font,
            text_color="white"
        )
        self.title_label.pack(pady=15)

    def _create_button_frame(self):
        self.btn_frame = ctk.CTkFrame(self.main_container)
        self.btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # ปุ่มเลือกกล้อง
        if self.available_cameras:
            self.camera_label = ctk.CTkLabel(self.btn_frame, text="เลือกกล้อง:", font=self.text_font)
            self.camera_label.pack(side="left", padx=(10, 5), pady=10)
            
            camera_options = [f"กล้อง {i}" for i in self.available_cameras]
            self.camera_combo = ctk.CTkComboBox(
                self.btn_frame,
                values=camera_options,
                command=self.on_camera_select,
                width=120,
                font=self.text_font
            )
            self.camera_combo.pack(side="left", padx=5, pady=10)
            self.camera_combo.set(camera_options[0] if camera_options else "ไม่มีกล้อง")
        
        # ปุ่มเปิด/ปิดกล้อง
        self.camera_btn = ctk.CTkButton(
            self.btn_frame, 
            text="📹 เปิดกล้อง", 
            command=self.toggle_camera,
            font=self.button_font,
            height=40,
            fg_color=self.secondary_color,
            hover_color=self.primary_color
        )
        self.camera_btn.pack(side="left", padx=10, pady=10)
        
        # ปุ่มตั้งค่าการแสดงผล
        self.config_btn = ctk.CTkButton(
            self.btn_frame, 
            text="⚙️ ตั้งค่าการแสดงผล", 
            command=self.show_config_dialog,
            font=self.button_font,
            height=40,
            fg_color=self.secondary_color,
            hover_color=self.primary_color
        )
        self.config_btn.pack(side="left", padx=5, pady=10)
        
        # ปุ่มบันทึกผลลัพธ์
        self.save_btn = ctk.CTkButton(
            self.btn_frame, 
            text="💾 บันทึกผลลัพธ์", 
            command=self.save_results,
            state="disabled",
            font=self.button_font,
            height=40,
            fg_color=self.secondary_color,
            hover_color=self.primary_color
        )
        self.save_btn.pack(side="right", padx=10, pady=10)

    def _create_content_frame(self):
        """สร้าง content frame ที่สามารถกำหนดค่าได้"""
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        
        # กำหนดค่า grid ตามจำนวนคอลัมน์
        if self.show_result_panel and self.content_columns >= 2:
            self.content_frame.grid_columnconfigure(0, weight=3)
            self.content_frame.grid_columnconfigure(1, weight=1)
        else:
            self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Frame สำหรับแสดงรูป/กล้อง
        self.image_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        if self.show_result_panel and self.content_columns >= 2:
            self.image_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        else:
            self.image_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # สร้าง drop zone frame
        self.drop_frame = ctk.CTkFrame(
            self.image_frame, 
            corner_radius=8, 
            fg_color=("gray90", "gray20"),
            border_width=2,
            border_color=("gray80", "gray30")
        )
        self.drop_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label สำหรับแสดงรูป/วิดีโอ
        self.image_label = ctk.CTkLabel(
            self.drop_frame, 
            text="ลากไฟล์รูปมาวางที่นี่ หรือ\nคลิกปุ่มด้านล่างเพื่อเลือกรูปทุเรียน\nหรือเปิดกล้องเพื่อวิเคราะห์แบบเรียลไทม์", 
            font=self.text_font
        )
        self.image_label.pack(fill="both", expand=True)
        
        # สถานะ FPS สำหรับกล้อง
        self.fps_label = ctk.CTkLabel(
            self.drop_frame,
            text="",
            font=CTkFont(family="Consolas", size=12),
            text_color="green"
        )
        self.fps_label.place(relx=0.02, rely=0.02)
        
        # ปุ่มเลือกรูปภาพ
        self.select_btn = ctk.CTkButton(
            self.drop_frame, 
            text="📂 เลือกรูปภาพ", 
            command=self.select_image,
            font=self.button_font,
            height=40,
            width=200,
            fg_color=self.secondary_color,
            hover_color=self.primary_color
        )
        self.select_btn.place(relx=0.5, rely=0.6, anchor="center")
        
        # ตั้งค่า drag and drop
        self._setup_drag_drop()
        
        # Frame สำหรับผลการวิเคราะห์ (ถ้าเปิดใช้งาน)
        if self.show_result_panel and self.content_columns >= 2:
            self._create_result_panel()
        
        # บันทึกขนาดของ frame
        self.image_frame.bind("<Configure>", self.on_frame_configure)

    def _create_result_panel(self):
        """สร้างแผงแสดงผลการวิเคราะห์"""
        self.result_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.result_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        
        # หัวข้อผลการวิเคราะห์
        self.result_title = ctk.CTkLabel(
            self.result_frame, 
            text="ผลการวิเคราะห์แบบเรียลไทม์", 
            font=CTkFont(family="Helvetica", size=18, weight="bold")
        )
        self.result_title.pack(pady=(15,5), padx=10)
        
        # Textbox สำหรับแสดงผลลัพธ์ข้อความ
        self.result_text = ctk.CTkTextbox(
            self.result_frame, 
            font=self.result_font, 
            corner_radius=5,
            wrap="word"
        )
        self.result_text.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        # ตั้งข้อความเริ่มต้น
        self.result_text.insert("1.0", "ยังไม่มีข้อมูลการวิเคราะห์\n\nเปิดกล้องเพื่อเริ่มการวิเคราะห์แบบเรียลไทม์")
        self.result_text.configure(state="disabled")

    def show_config_dialog(self):
        config = load_config()

        config_window = ctk.CTkToplevel(self)
        config_window.title("ตั้งค่าการแสดงผล")
        config_window.geometry("450x450")
        config_window.transient(self)
        
        # Wait for the window to be visible before grabbing focus
        config_window.after(10, lambda: config_window.grab_set())

        entries = {}

        def add_config_entry(section, key, label_text, row, col, widget_type="entry", options=None):
            ctk.CTkLabel(config_window, text=label_text).grid(row=row*2, column=col, sticky="w", padx=10, pady=(10, 0))
            
            var = ctk.StringVar(value=config[section][key] if section in config and key in config[section] else "")
            
            if widget_type == "combo" and options is not None:
                widget = ctk.CTkComboBox(config_window, values=options, variable=var)
                widget.grid(row=row*2+1, column=col, sticky="we", padx=10, pady=(0, 10))
            else:
                widget = ctk.CTkEntry(config_window, textvariable=var, width=80)
                widget.grid(row=row*2+1, column=col, sticky="we", padx=10, pady=(0, 10))
            
            entries[(section, key)] = var

        # ซ้ายคอลัมน์ (col=0)
        add_config_entry("Rendering", "line_thickness", "ความหนาเส้นขอบ (line_thickness):", row=0, col=0)
        add_config_entry("Rendering", "text_size", "ขนาดตัวอักษร (text_size):", row=1, col=0)
        add_config_entry("Rendering", "text_bold", "ความหนาอักษร (text_bold):", row=2, col=0)

        # ขวาคอลัมน์ (col=1)
        add_config_entry("Rendering", "point_size", "ขนาดจุด (point_size):", row=0, col=1)
        add_config_entry("Grading", "distance_threshold", "ค่าเกณฑ์ระยะห่าง (distance_threshold):", row=1, col=1)
        add_config_entry("Grading", "adj", "ค่าความลึกการตรวจ (adj):", row=2, col=1)

        add_config_entry("Camera", "fps", "FPS กล้อง:", row=3, col=0, widget_type="combo", options=["15", "24", "30", "60"])
        
        # ปุ่มตกลง แบบเต็มแถว
        def apply_config():
            for (section, key), var in entries.items():
                config[section][key] = var.get()
            save_config(config)

            self.fps = int(config['Camera']['fps'])
            self.frame_interval = 1.0 / self.fps

            config_window.destroy()

        ctk.CTkButton(config_window, text="ตกลง", command=apply_config).grid(row=10, column=0, columnspan=2, pady=20, padx=10, sticky="we")

        # กำหนดคอลัมน์ให้ขยายได้
        config_window.grid_columnconfigure(0, weight=1)
        config_window.grid_columnconfigure(1, weight=1)

    def on_camera_select(self, selection):
        """เมื่อเลือกกล้องใหม่"""
        camera_idx = int(selection.split()[-1])
        if camera_idx in self.available_cameras:
            self.selected_camera_idx = camera_idx
            if self.camera_active:
                self.stop_camera()
                time.sleep(0.5)  # รอให้กล้องเก่าปิดก่อน
                self.start_camera()

    def toggle_camera(self):
        """เปิด/ปิดกล้อง"""
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def start_camera(self):
        """เริ่มต้นกล้อง"""
        if not self.available_cameras:
            self.status_var.set("ไม่พบกล้องในระบบ")
            return
        
        try:
            self.camera = cv2.VideoCapture(self.selected_camera_idx)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            if not self.camera.isOpened():
                self.status_var.set("ไม่สามารถเปิดกล้องได้")
                return
            
            self.camera_active = True
            self.camera_btn.configure(text="⏹️ ปิดกล้อง")
            self.select_btn.place_forget()  # ซ่อนปุ่มเลือกรูป
            
            # เริ่ม thread สำหรับแสดงวิดีโอ
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
            
            self.status_var.set(f"เปิดกล้อง {self.selected_camera_idx} เรียบร้อยแล้ว")
            
        except Exception as e:
            self.status_var.set(f"เกิดข้อผิดพลาดในการเปิดกล้อง: {str(e)}")

    def stop_camera(self):
        """หยุดกล้อง"""
        self.camera_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_btn.configure(text="📹 เปิดกล้อง")
        self.fps_label.configure(text="")
        
        # แสดงปุ่มเลือกรูปอีกครั้ง
        self.reset_image_area()
        
        self.status_var.set("ปิดกล้องแล้ว")

    def _camera_loop(self):
        """Loop หลักสำหรับการแสดงผลจากกล้อง"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # คำนวณ FPS จริง
                fps_counter += 1
                current_time = time.time()
                
                if current_time - fps_start_time >= 1.0:
                    actual_fps = fps_counter / (current_time - fps_start_time)
                    self.after(0, lambda: self.fps_label.configure(text=f"FPS: {actual_fps:.1f}"))
                    fps_counter = 0
                    fps_start_time = current_time
                
                # แปลงสี BGR เป็น RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # วิเคราะห์เฟรมทุก analysis_interval วินาที
                if current_time - self.last_analysis_time >= self.analysis_interval:
                    self.last_analysis_time = current_time
                    self._analyze_camera_frame(frame_rgb.copy())
                
                # แสดงเฟรม
                # self.after(0, lambda f=frame_rgb: self._update_camera_display(f))
                
                # รอตามค่า FPS ที่กำหนด
                time.sleep(self.frame_interval)
                
            except Exception as e:
                print(f"Camera loop error: {e}")
                break
        
        # ทำความสะอาดเมื่อออกจาก loop
        if self.camera:
            self.camera.release()

    def _update_camera_display(self, frame):
        """อัพเดตการแสดงผลจากกล้อง"""
        try:
            self.original_image = frame
            self.update_image_display()
        except Exception as e:
            print(f"Display update error: {e}")

    def _analyze_camera_frame(self, frame):
        """วิเคราะห์เฟรมจากกล้องแบบ async"""
        def analyze():
            try:
                # บันทึกเฟรมชั่วคราว
                temp_path = "temp_camera_frame.jpg"
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(temp_path, frame_bgr)
                
                # วิเคราะห์
                img_result, text_result = process_image(temp_path)

                if img_result is not None:
                    self.show_image(img_result)
                
                # อัพเดต UI ใน main thread
                self.after(0, lambda: self._update_realtime_result(text_result))
                
                # ลบไฟล์ชั่วคราว
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            except Exception as e:
                self.after(0, lambda e=e: self.status_var.set(f"ข้อผิดพลาดในการวิเคราะห์: {str(e)}"))
        
        # รันการวิเคราะห์ใน thread แยก
        threading.Thread(target=analyze, daemon=True).start()

    def _update_realtime_result(self, text_result):
        """อัพเดตผลการวิเคราะห์แบบเรียลไทม์"""
        if hasattr(self, 'result_text') and self.show_result_panel:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                formatted_result = f"🕒 {current_time}\n{text_result}\n{'-'*30}\n"
                
                self.result_text.configure(state="normal")
                
                # เก็บผลลัพธ์เก่าไม่เกิน 10 รายการ
                current_content = self.result_text.get("1.0", "end")
                lines = current_content.split('\n')
                if len(lines) > 200:  # จำกัดจำนวนบรรทัด
                    self.result_text.delete("1.0", "end")
                
                self.result_text.insert("1.0", formatted_result)
                self.result_text.configure(state="normal")
                
                # เปิดใช้งานปุ่มบันทึก
                self.save_btn.configure(state="normal")
                
            except Exception as e:
                print(f"Result update error: {e}")

    def _setup_drag_drop(self):
        """ตั้งค่าฟังก์ชันสำหรับรองรับการลากและวางไฟล์"""
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop_file)
        
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_file)
        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind('<<Drop>>', self.drop_file)
    
    def drop_file(self, event):
        """เมื่อมีการปล่อยไฟล์ลงในพื้นที่รับไฟล์"""
        # หยุดกล้องก่อนถ้ากำลังทำงาน
        if self.camera_active:
            self.stop_camera()
        
        self.drop_frame.configure(fg_color=("lightblue", "darkblue"), border_color=self.primary_color)
        self.after(100, lambda: self.drop_frame.configure(fg_color=("gray90", "gray20"), border_color=("gray80", "gray30")))
        
        file_path = event.data.strip('{}').replace('"', '')
        file_extension = os.path.splitext(file_path)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        if file_extension in valid_extensions:
            self.image_path = file_path
            self.process_selected_image()
        else:
            self.status_var.set(f"ไฟล์ไม่ใช่รูปภาพที่รองรับ รองรับเฉพาะ {', '.join(valid_extensions)}")

    def select_image(self):
        # หยุดกล้องก่อนถ้ากำลังทำงาน
        if self.camera_active:
            self.stop_camera()
            
        file_path = filedialog.askopenfilename(
            title="เลือกรูปภาพทุเรียน",
            filetypes=[("ไฟล์รูปภาพ", "*.jpg *.png *.jpeg")]
        )
        
        if file_path:
            self.image_path = file_path
            self.process_selected_image()

    def process_selected_image(self):
        """ประมวลผลรูปภาพที่เลือก"""
        self.status_var.set(f"กำลังโหลดรูปภาพ: {os.path.basename(self.image_path)}")
        self.update()
        
        img = cv2.imread(self.image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.original_image = img
        
        self.select_btn.place_forget()
        self.update_image_display()
        
        if hasattr(self, 'result_text') and self.show_result_panel:
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", "กำลังวิเคราะห์รูปภาพ... โปรดรอสักครู่")
            self.result_text.configure(state="disabled")
        
        self.status_var.set(f"กำลังวิเคราะห์: {os.path.basename(self.image_path)}")
        self.after(100, self.analyze_image)

    def on_frame_configure(self, event):
        if self.original_image is not None:
            self.update_image_display()

    def update_image_display(self):
        if self.original_image is None:
            return
        
        frame_width = self.drop_frame.winfo_width()
        frame_height = self.drop_frame.winfo_height()
        
        if frame_width <= 1 or frame_height <= 1:
            frame_width = 600
            frame_height = 600
        
        img_height, img_width = self.original_image.shape[:2]
        ratio = min((frame_width - 20) / img_width, (frame_height - 20) / img_height)
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        try:
            resample_mode = Image.Resampling.LANCZOS
        except AttributeError:
            resample_mode = Image.ANTIALIAS
        
        img_pil = Image.fromarray(self.original_image)
        
        if img_pil.mode == 'RGBA':
            background = Image.new('RGB', img_pil.size, (255, 255, 255))
            background.paste(img_pil, mask=img_pil.split()[3])
            img_pil = background
        
        try:
            img_pil = ImageOps.autocontrast(img_pil, cutoff=0.5)
            img_pil = img_pil.filter(ImageFilter.SHARPEN)
            img_with_border = ImageOps.expand(img_pil, border=2, fill='white')
        except Exception as e:
            self.status_var.set(f"ไม่สามารถปรับแต่งรูปภาพ: {str(e)}")
            img_with_border = img_pil
        
        img_resized = img_with_border.resize((new_width, new_height), resample_mode)
        
        img_ctk = CTkImage(light_image=img_resized, 
                           dark_image=img_resized, 
                           size=(new_width, new_height))
        
        self.image_label.configure(image=img_ctk, text="")
        self.image_label.image = img_ctk

    def show_image(self, path_or_array):
        if isinstance(path_or_array, str):
            img = cv2.imread(path_or_array)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img = path_or_array.copy()
            if img is not None:
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                elif img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif img.shape[2] == 3:
                    if np.max(img) <= 1.0:
                        img = (img * 255).astype(np.uint8)
        
        if img is not None:
            self.original_image = img
            self.update_image_display()
        else:
            self.status_var.set("ไม่สามารถโหลดรูปภาพได้")
            self.image_label.configure(image=None, text="ไม่สามารถโหลดรูปภาพได้")
            self.select_btn.place(relx=0.5, rely=0.5, anchor="center")

    def reset_image_area(self):
        """รีเซ็ตพื้นที่แสดงรูปกลับไปยังสถานะเริ่มต้น"""
        self.image_label.configure(image=None, 
                                 text="ลากไฟล์รูปมาวางที่นี่ หรือ\nคลิกปุ่มด้านล่างเพื่อเลือกรูปทุเรียน\nหรือเปิดกล้องเพื่อวิเคราะห์แบบเรียลไทม์")
        self.select_btn.place(relx=0.5, rely=0.5, anchor="center")

    def analyze_image(self):
        if self.image_path and not self.is_analyzing:
            self.is_analyzing = True
            
            self.status_var.set("กำลังวิเคราะห์รูปภาพ... โปรดรอสักครู่")
            self.update()
            
            try:
                img_result, text_result = process_image(self.image_path)
                
                if img_result is not None:
                    self.show_image(img_result)
                
                if hasattr(self, 'result_text') and self.show_result_panel:
                    self.result_text.configure(state="normal")
                    self.result_text.delete("1.0", "end")
                    
                    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    formatted_result = f"📅 วันที่วิเคราะห์: {current_time}\n\n"
                    formatted_result += text_result
                    
                    self.result_text.insert("1.0", formatted_result)
                    self.result_text.configure(state="normal")
                
                # บันทึกประวัติการวิเคราะห์
                self.result_history.append({
                    'path': self.image_path,
                    'time': current_time,
                    'result': text_result
                })
                
                self.save_btn.configure(state="normal")
                self.status_var.set("วิเคราะห์เสร็จสมบูรณ์")
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                
                if hasattr(self, 'result_text') and self.show_result_panel:
                    self.result_text.configure(state="normal")
                    self.result_text.delete("1.0", "end")
                    self.result_text.insert("1.0", f"เกิดข้อผิดพลาด: {str(e)}\n\nรายละเอียด:\n{error_detail}")
                    self.result_text.configure(state="normal")
                
                self.status_var.set("เกิดข้อผิดพลาดในการวิเคราะห์")
                print(f"Error: {error_detail}")
            
            self.is_analyzing = False
            
    def save_results(self):
        """บันทึกผลการวิเคราะห์ไปยังไฟล์ข้อความ"""
        if not self.result_history:
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                title="บันทึกผลการวิเคราะห์"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("===== รายงานการวิเคราะห์คุณภาพทุเรียน =====\n\n")
                    
                    for idx, entry in enumerate(self.result_history, 1):
                        file.write(f"รายการที่ {idx}\n")
                        file.write(f"ไฟล์: {entry['path']}\n")
                        file.write(f"เวลา: {entry['time']}\n")
                        file.write(f"ผลการวิเคราะห์:\n{entry['result']}\n")
                        file.write("-" * 50 + "\n\n")
                
                self.status_var.set(f"บันทึกผลการวิเคราะห์ไปยัง {os.path.basename(file_path)} เรียบร้อยแล้ว")
        except Exception as e:
            self.status_var.set(f"เกิดข้อผิดพลาดในการบันทึกไฟล์: {str(e)}")

    def __del__(self):
        """ทำความสะอาดเมื่อปิดแอปพลิเคชัน"""
        if hasattr(self, 'camera_active') and self.camera_active:
            self.stop_camera()


if __name__ == "__main__":
    app = DurianGraderApp()
    app.mainloop()