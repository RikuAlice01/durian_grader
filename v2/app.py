import customtkinter as ctk
from customtkinter import CTkImage, CTkFont
import tkinterdnd2
from tkinterdnd2 import DND_FILES
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageOps
import numpy as np
import os
from datetime import datetime
import threading

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
        self.title("Enhanced Durian Grading System")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0)
        self.main_container.grid_rowconfigure(1, weight=0)
        self.main_container.grid_rowconfigure(2, weight=1)

        # ตัวแปรเก็บข้อมูล
        self.image_paths = {
            'top': None,
            'segments_ab': None,
            'segments_bc': None,
            'segments_cd': None,
            'segments_de': None,
            'segments_ea': None
        }
        self.original_images = {}
        self.processed_images = {}
        self.analysis_results = {}
        self.result_history = []
        self.is_analyzing = False
        self.camera_active = {}
        self.camera_caps = {}

        # กำหนดสีและฟอนต์
        self.primary_color = "#4CAF50"
        self.secondary_color = "#689F38"
        self.header_font = CTkFont(family="Helvetica", size=28, weight="bold")
        self.button_font = CTkFont(family="Helvetica", size=12, weight="bold")
        self.text_font = CTkFont(family="Helvetica", size=11)
        self.result_font = CTkFont(family="Consolas", size=12)
        
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

    def _create_header_frame(self):
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color=self.primary_color, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🍈 Enhanced AI Durian Grading System", 
            font=self.header_font,
            text_color="white"
        )
        self.title_label.pack(pady=15)

    def _create_button_frame(self):
        self.btn_frame = ctk.CTkFrame(self.main_container)
        self.btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # ปุ่มวิเคราะห์
        self.analyze_btn = ctk.CTkButton(
            self.btn_frame, 
            text="🔍 วิเคราะห์ทั้งหมด", 
            command=self.analyze_all_images,
            state="disabled",
            font=self.button_font,
            height=40,
            fg_color=self.primary_color,
            hover_color=self.secondary_color
        )
        self.analyze_btn.pack(side="left", padx=10, pady=10)
        
        # ปุ่มล้างข้อมูล
        self.clear_btn = ctk.CTkButton(
            self.btn_frame, 
            text="🗑️ ล้างข้อมูล", 
            command=self.clear_all_data,
            font=self.button_font,
            height=40,
            fg_color="red",
            hover_color="darkred"
        )
        self.clear_btn.pack(side="left", padx=10, pady=10)
        
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
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.content_frame.grid_columnconfigure(0, weight=2)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # สร้าง Notebook สำหรับแท็บต่างๆ
        self.notebook = ctk.CTkTabview(self.content_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # แท็บสำหรับการนำเข้ารูปภาพ
        self.notebook.add("นำเข้ารูปภาพ")
        self.notebook.add("ผลการวิเคราะห์")
        
        self._create_image_input_tab()
        self._create_analysis_tab()
        
        # Frame สำหรับผลการวิเคราะห์
        self.result_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.result_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        
        self._create_result_panel()

    def _create_image_input_tab(self):
        input_frame = self.notebook.tab("นำเข้ารูปภาพ")
        
        # สร้างกริดสำหรับรูปภาพ 6 รูป (2x3)
        input_frame.grid_columnconfigure((0, 1, 2), weight=1)
        input_frame.grid_rowconfigure((0, 1), weight=1)
        
        # ข้อมูลรูปภาพ
        image_configs = [
            ("top", "รูปที่ 1: ด้านบน", 0, 0),
            ("segments_ab", "รูปที่ 2: Segment A-B", 0, 1),
            ("segments_bc", "รูปที่ 3: Segment B-C", 0, 2),
            ("segments_cd", "รูปที่ 4: Segment C-D", 1, 0),
            ("segments_de", "รูปที่ 5: Segment D-E", 1, 1),
            ("segments_ea", "รูปที่ 6: Segment E-A", 1, 2)
        ]
        
        self.image_frames = {}
        self.image_labels = {}
        self.camera_buttons = {}
        self.file_buttons = {}
        
        for img_key, title, row, col in image_configs:
            # สร้าง frame สำหรับแต่ละรูป
            frame = ctk.CTkFrame(input_frame, corner_radius=10)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            frame.grid_rowconfigure(1, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            
            # หัวข้อ
            title_label = ctk.CTkLabel(frame, text=title, font=self.button_font)
            title_label.grid(row=0, column=0, pady=(10, 5))
            
            # พื้นที่แสดงรูป
            img_display = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"))
            img_display.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
            
            img_label = ctk.CTkLabel(
                img_display, 
                text="ไม่มีรูปภาพ", 
                font=self.text_font
            )
            img_label.pack(fill="both", expand=True)
            
            # ปุ่มควบคุม
            btn_frame = ctk.CTkFrame(frame)
            btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
            btn_frame.grid_columnconfigure((0, 1), weight=1)
            
            # ปุ่มเลือกไฟล์
            file_btn = ctk.CTkButton(
                btn_frame, 
                text="📁 เลือกไฟล์",
                command=lambda k=img_key: self.select_image_file(k),
                font=self.text_font,
                height=30
            )
            file_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
            
            # ปุ่มกล้อง
            camera_btn = ctk.CTkButton(
                btn_frame, 
                text="📷 กล้อง",
                command=lambda k=img_key: self.toggle_camera(k),
                font=self.text_font,
                height=30,
                fg_color="blue",
                hover_color="darkblue"
            )
            camera_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
            
            # เก็บ reference
            self.image_frames[img_key] = frame
            self.image_labels[img_key] = img_label
            self.camera_buttons[img_key] = camera_btn
            self.file_buttons[img_key] = file_btn
            self.camera_active[img_key] = False
            
            # ตั้งค่า drag and drop
            self._setup_drag_drop_for_frame(img_display, img_key)

    def _create_analysis_tab(self):
        analysis_frame = self.notebook.tab("ผลการวิเคราะห์")
        
        # สร้างตารางแสดงผล 2x3
        analysis_frame.grid_columnconfigure((0, 1, 2), weight=1)
        analysis_frame.grid_rowconfigure((0, 1), weight=1)
        
        self.analysis_labels = {}
        
        segments = ['A', 'B', 'C', 'D', 'E', 'F']
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        
        for segment, (row, col) in zip(segments, positions):
            frame = ctk.CTkFrame(analysis_frame, corner_radius=10)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
            title = ctk.CTkLabel(frame, text=f"Segment {segment}", font=self.button_font)
            title.pack(pady=(10, 5))
            
            result_label = ctk.CTkLabel(
                frame, 
                text="ยังไม่ได้วิเคราะห์", 
                font=self.text_font,
                wraplength=200
            )
            result_label.pack(fill="both", expand=True, padx=10, pady=10)
            
            self.analysis_labels[segment] = result_label

    def _create_result_panel(self):
        # หัวข้อผลการวิเคราะห์
        self.result_title = ctk.CTkLabel(
            self.result_frame, 
            text="สรุปผลการวิเคราะห์", 
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
        self.result_text.insert("1.0", "ยังไม่มีข้อมูลการวิเคราะห์\n\nกรุณานำเข้ารูปภาพและกดปุ่มวิเคราะห์")
        self.result_text.configure(state="disabled")

    def _setup_drag_drop_for_frame(self, frame, img_key):
        """ตั้งค่า drag and drop สำหรับ frame แต่ละรูป"""
        frame.drop_target_register(DND_FILES)
        frame.dnd_bind('<<Drop>>', lambda event, key=img_key: self.drop_file(event, key))

    def drop_file(self, event, img_key):
        """เมื่อมีการปล่อยไฟล์ลงในพื้นที่รับไฟล์"""
        file_path = event.data.strip('{}').replace('"', '')
        
        # ตรวจสอบว่าเป็นไฟล์รูปหรือไม่
        file_extension = os.path.splitext(file_path)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        if file_extension in valid_extensions:
            self.image_paths[img_key] = file_path
            self.load_and_display_image(img_key, file_path)
            self.check_analyze_button_state()
        else:
            self.status_var.set(f"ไฟล์ไม่ใช่รูปภาพที่รองรับ รองรับเฉพาะ {', '.join(valid_extensions)}")

    def select_image_file(self, img_key):
        """เลือกไฟล์รูปภาพ"""
        file_path = filedialog.askopenfilename(
            title=f"เลือกรูปภาพสำหรับ {img_key}",
            filetypes=[("ไฟล์รูปภาพ", "*.jpg *.png *.jpeg *.bmp")]
        )
        
        if file_path:
            self.image_paths[img_key] = file_path
            self.load_and_display_image(img_key, file_path)
            self.check_analyze_button_state()

    def toggle_camera(self, img_key):
        """เปิด/ปิดกล้อง"""
        if not self.camera_active[img_key]:
            self.start_camera(img_key)
        else:
            self.stop_camera(img_key)

    def start_camera(self, img_key):
        """เริ่มการใช้งานกล้อง"""
        # ให้ผู้ใช้เลือกกล้อง
        camera_index = self.select_camera()
        if camera_index is None:
            return
        
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเปิดกล้องได้")
                return
            
            self.camera_caps[img_key] = cap
            self.camera_active[img_key] = True
            self.camera_buttons[img_key].configure(text="📷 หยุดกล้อง", fg_color="red")
            
            # เริ่ม thread สำหรับแสดงภาพจากกล้อง
            threading.Thread(target=self.camera_loop, args=(img_key,), daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการเปิดกล้อง: {str(e)}")

    def stop_camera(self, img_key):
        """หยุดการใช้งานกล้อง"""
        self.camera_active[img_key] = False
        if img_key in self.camera_caps:
            self.camera_caps[img_key].release()
            del self.camera_caps[img_key]
        
        self.camera_buttons[img_key].configure(text="📷 กล้อง", fg_color="blue")

    def select_camera(self):
        """ให้ผู้ใช้เลือกกล้อง"""
        # ตรวจหากล้องที่มีอยู่
        available_cameras = []
        for i in range(5):  # ตรวจสอบกล้อง 5 ตัวแรก
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        if not available_cameras:
            messagebox.showerror("ข้อผิดพลาด", "ไม่พบกล้องที่ใช้งานได้")
            return None
        
        if len(available_cameras) == 1:
            return available_cameras[0]
        
        # สร้างหน้าต่างเลือกกล้อง
        camera_window = ctk.CTkToplevel(self)
        camera_window.title("เลือกกล้อง")
        camera_window.geometry("300x200")
        camera_window.transient(self)
        camera_window.grab_set()
        
        selected_camera = None
        
        def select_cam(index):
            nonlocal selected_camera
            selected_camera = index
            camera_window.destroy()
        
        ctk.CTkLabel(camera_window, text="เลือกกล้องที่ต้องการใช้:", font=self.button_font).pack(pady=20)
        
        for i, cam_index in enumerate(available_cameras):
            btn = ctk.CTkButton(
                camera_window, 
                text=f"กล้อง {cam_index}",
                command=lambda idx=cam_index: select_cam(idx)
            )
            btn.pack(pady=5)
        
        self.wait_window(camera_window)
        return selected_camera

    def camera_loop(self, img_key):
        """ลูปสำหรับแสดงภาพจากกล้อง"""
        while self.camera_active[img_key] and img_key in self.camera_caps:
            ret, frame = self.camera_caps[img_key].read()
            if ret:
                # แปลงและแสดงภาพ
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.display_camera_frame(img_key, frame_rgb)
                
                # เพิ่มปุ่มถ่ายภาพ (overlay)
                self.add_capture_button(img_key, frame_rgb)
            
            # หน่วงเวลา
            self.after(30)  # ~33 FPS

    def display_camera_frame(self, img_key, frame):
        """แสดงเฟรมจากกล้อง"""
        try:
            # ปรับขนาดภาพให้เหมาะสม
            height, width = frame.shape[:2]
            max_size = 200
            
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            
            frame_resized = cv2.resize(frame, (new_width, new_height))
            
            # แปลงเป็น PIL Image
            img_pil = Image.fromarray(frame_resized)
            
            # สร้าง CTkImage
            img_ctk = CTkImage(light_image=img_pil, dark_image=img_pil, size=(new_width, new_height))
            
            # แสดงในหน้าต่าง
            self.image_labels[img_key].configure(image=img_ctk, text="")
            self.image_labels[img_key].image = img_ctk
            
        except Exception as e:
            print(f"Error displaying camera frame: {e}")

    def add_capture_button(self, img_key, frame):
        """เพิ่มปุ่มถ่ายภาพ"""
        # สร้างปุ่มถ่ายภาพถ้ายังไม่มี
        if not hasattr(self, 'capture_buttons'):
            self.capture_buttons = {}
        
        if img_key not in self.capture_buttons:
            capture_btn = ctk.CTkButton(
                self.image_labels[img_key],
                text="📸 ถ่ายภาพ",
                command=lambda: self.capture_image(img_key, frame),
                width=80,
                height=30,
                font=CTkFont(size=10)
            )
            capture_btn.place(relx=0.5, rely=0.9, anchor="center")
            self.capture_buttons[img_key] = capture_btn

    def capture_image(self, img_key, frame):
        """ถ่ายภาพจากกล้อง"""
        # บันทึกภาพ
        self.original_images[img_key] = frame.copy()
        
        # หยุดกล้อง
        self.stop_camera(img_key)
        
        # แสดงภาพที่ถ่าย
        self.display_captured_image(img_key, frame)
        
        # ตรวจสอบสถานะปุ่มวิเคราะห์
        self.check_analyze_button_state()
        
        self.status_var.set(f"ถ่ายภาพสำหรับ {img_key} เรียบร้อยแล้ว")

    def display_captured_image(self, img_key, frame):
        """แสดงภาพที่ถ่ายแล้ว"""
        try:
            # ปรับขนาดภาพ
            height, width = frame.shape[:2]
            max_size = 200
            
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            
            frame_resized = cv2.resize(frame, (new_width, new_height))
            img_pil = Image.fromarray(frame_resized)
            
            # เพิ่มขอบให้ภาพ
            img_with_border = ImageOps.expand(img_pil, border=3, fill='green')
            
            img_ctk = CTkImage(light_image=img_with_border, dark_image=img_with_border, 
                             size=(new_width + 6, new_height + 6))
            
            self.image_labels[img_key].configure(image=img_ctk, text="")
            self.image_labels[img_key].image = img_ctk
            
            # ลบปุ่มถ่ายภาพ
            if hasattr(self, 'capture_buttons') and img_key in self.capture_buttons:
                self.capture_buttons[img_key].destroy()
                del self.capture_buttons[img_key]
                
        except Exception as e:
            print(f"Error displaying captured image: {e}")

    def load_and_display_image(self, img_key, file_path):
        """โหลดและแสดงรูปภาพจากไฟล์"""
        try:
            # อ่านรูปภาพ
            img = cv2.imread(file_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.original_images[img_key] = img_rgb
            
            # แสดงรูปภาพ
            self.display_image_in_label(img_key, img_rgb)
            
            self.status_var.set(f"โหลดรูปภาพ {img_key} เรียบร้อยแล้ว")
            
        except Exception as e:
            self.status_var.set(f"เกิดข้อผิดพลาดในการโหลดรูปภาพ: {str(e)}")

    def display_image_in_label(self, img_key, img_array):
        """แสดงรูปภาพใน label"""
        try:
            # ปรับขนาดภาพ
            height, width = img_array.shape[:2]
            max_size = 200
            
            if width > height:
                new_width = max_size
                new_height = int(height * max_size / width)
            else:
                new_height = max_size
                new_width = int(width * max_size / height)
            
            img_resized = cv2.resize(img_array, (new_width, new_height))
            img_pil = Image.fromarray(img_resized)
            
            # เพิ่มขอบ
            img_with_border = ImageOps.expand(img_pil, border=2, fill='blue')
            
            img_ctk = CTkImage(light_image=img_with_border, dark_image=img_with_border, 
                             size=(new_width + 4, new_height + 4))
            
            self.image_labels[img_key].configure(image=img_ctk, text="")
            self.image_labels[img_key].image = img_ctk
            
        except Exception as e:
            print(f"Error displaying image: {e}")

    def check_analyze_button_state(self):
        """ตรวจสอบว่าควรเปิดใช้งานปุ่มวิเคราะห์หรือไม่"""
        # ตรวจสอบว่ามีรูปภาพอย่างน้อย 1 รูป
        has_images = any(img_key in self.original_images for img_key in self.image_paths.keys())
        
        if has_images:
            self.analyze_btn.configure(state="normal")
        else:
            self.analyze_btn.configure(state="disabled")

    def analyze_all_images(self):
        """วิเคราะห์รูปภาพทั้งหมด"""
        if self.is_analyzing:
            return
        
        self.is_analyzing = True
        self.analyze_btn.configure(state="disabled", text="🔍 กำลังวิเคราะห์...")
        self.status_var.set("กำลังวิเคราะห์รูปภาพทั้งหมด...")
        
        # เริ่มการวิเคราะห์ใน thread แยก
        threading.Thread(target=self._analyze_thread, daemon=True).start()

    def _analyze_thread(self):
        """Thread สำหรับการวิเคราะห์"""
        try:
            results = {}
            
            # วิเคราะห์แต่ละรูป
            for img_key, img_array in self.original_images.items():
                if img_array is not None:
                    # บันทึกรูปชั่วคราว
                    temp_path = f"temp_{img_key}.jpg"
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(temp_path, img_bgr)
                    
                    # วิเคราะห์
                    processed_img, text_result = process_image(temp_path)
                    
                    if processed_img is not None:
                        self.processed_images[img_key] = processed_img
                        results[img_key] = text_result
                    
                    # ลบไฟล์ชั่วคราว
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            # คำนวณระยะห่างสำหรับแต่ละ segment
            segment_distances = self._calculate_segment_distances()
            
            # อัพเดท UI ใน main thread
            self.after(0, lambda: self._update_analysis_results(results, segment_distances))
            
        except Exception as e:
            self.after(0, lambda: self._handle_analysis_error(str(e)))

    def _calculate_segment_distances(self):
        """คำนวณระยะห่างสำหรับแต่ละ segment"""
        # ตัวอย่างการคำนวณ - ควรปรับให้เหมาะสมกับข้อมูลจริง
        segment_data = {
            'A': {'images': ['segments_ab', 'segments_ea'], 'distance': 0},
            'B': {'images': ['segments_ab', 'segments_bc'], 'distance': 0},
            'C': {'images': ['segments_bc', 'segments_cd'], 'distance': 0},
            'D': {'images': ['segments_cd', 'segments_de'], 'distance': 0},
            'E': {'images': ['segments_de', 'segments_ea'], 'distance': 0}
        }
        
        # คำนวณระยะห่างจากจุดกึ่งกลาง (จุดแดง) ไปยังจุดน้ำเงิน
        for segment, data in segment_data.items():
            distances = []
            for img_key in data['images']:
                if img_key in self.processed_images:
                    # ตัวอย่างการคำนวณระยะห่าง
                    # ในการใช้งานจริงควรใช้ข้อมูลจากการวิเคราะห์ภาพ
                    distance = np.random.uniform(10, 50)  # ตัวอย่าง
                    distances.append(distance)
            
            if distances:
                data['distance'] = np.mean(distances)
        
        return segment_data

    def _update_analysis_results(self, results, segment_distances):
        """อัพเดทผลการวิเคราะห์ใน UI"""
        # อัพเดทตารางผลลัพธ์
        for segment, data in segment_distances.items():
            if segment in self.analysis_labels:
                result_text = f"ระยะห่าง: {data['distance']:.2f} px\n"
                result_text += f"รูปที่ใช้: {', '.join(data['images'])}"
                self.analysis_labels[segment].configure(text=result_text)
        
        # อัพเดทผลรวม
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        summary = f"📅 วันที่วิเคราะห์: {current_time}\n\n"
        summary += "=== ผลการวิเคราะห์ระยะห่าง ===\n\n"
        
        for segment, data in segment_distances.items():
            summary += f"Segment {segment}: {data['distance']:.2f} px\n"
        
        summary += "\n=== รายละเอียดแต่ละรูป ===\n\n"
        for img_key, result in results.items():
            summary += f"{img_key}:\n{result}\n\n"
        
        self.result_text.insert("1.0", summary)
        self.result_text.configure(state="disabled")
        
        # บันทึกประวัติ
        self.result_history.append({
            'time': current_time,
            'segment_distances': segment_distances,
            'individual_results': results
        })
        
        # เปิดใช้งานปุ่มบันทึก
        self.save_btn.configure(state="normal")
        
        # รีเซ็ตปุ่มวิเคราะห์
        self.analyze_btn.configure(state="normal", text="🔍 วิเคราะห์ทั้งหมด")
        self.is_analyzing = False
        self.status_var.set("วิเคราะห์เสร็จสมบูรณ์")

    def _handle_analysis_error(self, error_msg):
        """จัดการข้อผิดพลาดในการวิเคราะห์"""
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", f"เกิดข้อผิดพลาดในการวิเคราะห์:\n{error_msg}")
        self.result_text.configure(state="disabled")
        
        self.analyze_btn.configure(state="normal", text="🔍 วิเคราะห์ทั้งหมด")
        self.is_analyzing = False
        self.status_var.set("เกิดข้อผิดพลาดในการวิเคราะห์")

    def clear_all_data(self):
        """ล้างข้อมูลทั้งหมด"""
        # หยุดกล้องทั้งหมด
        for img_key in list(self.camera_active.keys()):
            if self.camera_active[img_key]:
                self.stop_camera(img_key)
        
        # ล้างข้อมูลรูปภาพ
        self.image_paths = {key: None for key in self.image_paths.keys()}
        self.original_images.clear()
        self.processed_images.clear()
        self.analysis_results.clear()
        
        # รีเซ็ต UI
        for img_key, label in self.image_labels.items():
            label.configure(image=None, text="ไม่มีรูปภาพ")
        
        for segment, label in self.analysis_labels.items():
            label.configure(text="ยังไม่ได้วิเคราะห์")
        
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "ยังไม่มีข้อมูลการวิเคราะห์\n\nกรุณานำเข้ารูปภาพและกดปุ่มวิเคราะห์")
        self.result_text.configure(state="disabled")
        
        # ปิดใช้งานปุ่ม
        self.analyze_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        
        self.status_var.set("ล้างข้อมูลเรียบร้อยแล้ว")

    def save_results(self):
        """บันทึกผลการวิเคราะห์"""
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
                    file.write("===== รายงานการวิเคราะห์คุณภาพทุเรียนแบบ 6 รูป =====\n\n")
                    
                    for idx, entry in enumerate(self.result_history, 1):
                        file.write(f"รายการที่ {idx}\n")
                        file.write(f"เวลา: {entry['time']}\n\n")
                        
                        file.write("ผลการวิเคราะห์ระยะห่าง:\n")
                        for segment, data in entry['segment_distances'].items():
                            file.write(f"  Segment {segment}: {data['distance']:.2f} px\n")
                        
                        file.write("\nรายละเอียดแต่ละรูป:\n")
                        for img_key, result in entry['individual_results'].items():
                            file.write(f"  {img_key}: {result}\n")
                        
                        file.write("-" * 60 + "\n\n")
                
                self.status_var.set(f"บันทึกผลการวิเคราะห์ไปยัง {os.path.basename(file_path)} เรียบร้อยแล้ว")
        except Exception as e:
            self.status_var.set(f"เกิดข้อผิดพลาดในการบันทึกไฟล์: {str(e)}")

    def on_closing(self):
        """เมื่อปิดโปรแกรม"""
        # หยุดกล้องทั้งหมด
        for img_key in list(self.camera_active.keys()):
            if self.camera_active[img_key]:
                self.stop_camera(img_key)
        
        self.destroy()


if __name__ == "__main__":
    app = DurianGraderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()