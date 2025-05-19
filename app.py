import customtkinter as ctk
from customtkinter import CTkImage, CTkFont
import tkinterdnd2
from tkinterdnd2 import TkinterDnD, DND_FILES  # Ensure DND_FILES is imported correctly
from tkinter import filedialog, PhotoImage
import cv2
from PIL import Image, ImageOps, ImageFilter
import numpy as np
import os
from datetime import datetime
import tkinter as tk

from durian_grader import process_image  # ใช้จากโค้ดที่คุณเขียนไว้เดิมใน durian_grader.py

# ตั้งค่าธีมสีและรูปแบบ
ctk.set_appearance_mode("System")  # "System", "Dark" หรือ "Light"
ctk.set_default_color_theme("green")  # เปลี่ยนธีมเป็นสีเขียวให้เข้ากับทุเรียน

class DurianGraderApp(tkinterdnd2.TkinterDnD.Tk):  # Change base class to TkinterDnD.Tk
    def __init__(self):
        super().__init__()
        
        # Create a CustomTkinter frame as main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill='both', expand=True)

        # ตั้งค่าหน้าต่างหลัก
        self.title("Durian Grading System")
        self.geometry("1200x800")
        self.minsize(900, 700)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=0)
        self.main_container.grid_rowconfigure(1, weight=0)
        self.main_container.grid_rowconfigure(2, weight=1)

        # ตัวแปรเก็บข้อมูล
        self.image_path = None
        self.original_image = None
        self.result_history = []
        self.is_analyzing = False  # เพิ่มตัวแปรเพื่อติดตามสถานะการวิเคราะห์

        # กำหนดสีและฟอนต์
        self.primary_color = "#4CAF50"  # สีเขียว
        self.secondary_color = "#689F38"  # สีเขียวอ่อน
        self.header_font = CTkFont(family="Helvetica", size=28, weight="bold")
        self.button_font = CTkFont(family="Helvetica", size=14, weight="bold")
        self.text_font = CTkFont(family="Helvetica", size=13)
        self.result_font = CTkFont(family="Consolas", size=14)
        
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
        # สร้าง Frame หัวเว็บ
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color=self.primary_color, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        # โลโก้และชื่อแอพ
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🍈 AI Durian Grading System", 
            font=self.header_font,
            text_color="white"
        )
        self.title_label.pack(pady=15)

    def _create_button_frame(self):
        # Frame สำหรับปุ่มควบคุม
        self.btn_frame = ctk.CTkFrame(self.main_container)
        self.btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
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
        # Frame สำหรับแสดงรูปและผลลัพธ์
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.content_frame.grid_columnconfigure(0, weight=3)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Frame สำหรับแสดงรูป
        self.image_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.image_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # สร้าง drop zone frame พร้อมสีพื้นหลังที่จะเปลี่ยนเมื่อลากไฟล์มาวาง
        self.drop_frame = ctk.CTkFrame(
            self.image_frame, 
            corner_radius=8, 
            fg_color=("gray90", "gray20"),
            border_width=2,
            border_color=("gray80", "gray30")
        )
        self.drop_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label สำหรับแสดงรูป พร้อมข้อความเริ่มต้น
        self.image_label = ctk.CTkLabel(
            self.drop_frame, 
            text="ลากไฟล์รูปมาวางที่นี่ หรือ\nคลิกปุ่มด้านล่างเพื่อเลือกรูปทุเรียน", 
            font=self.text_font
        )
        self.image_label.pack(fill="both", expand=True)
        
        # สร้างปุ่มเลือกรูปภาพตรงกลางของพื้นที่แสดงรูป
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
        self.select_btn.place(relx=0.5, rely=0.5, anchor="center")
        
        # ตั้งค่า event handlers สำหรับ drag and drop
        self._setup_drag_drop()
        
        # Frame สำหรับผลการวิเคราะห์
        self.result_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.result_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        
        # หัวข้อผลการวิเคราะห์
        self.result_title = ctk.CTkLabel(
            self.result_frame, 
            text="ผลการวิเคราะห์", 
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
        self.result_text.insert("1.0", "ยังไม่มีข้อมูลการวิเคราะห์\n\nลากไฟล์รูปมาวางในพื้นที่แสดงรูป หรือคลิกปุ่มเลือกรูปภาพ")
        self.result_text.configure(state="disabled")
        
        # บันทึกขนาดของ frame
        self.image_frame.bind("<Configure>", self.on_frame_configure)

    def _setup_drag_drop(self):
        """ตั้งค่าฟังก์ชันสำหรับรองรับการลากและวางไฟล์ (drag and drop)"""
        # ลงทะเบียนพื้นที่รับไฟล์แบบ drop target
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.drop_file)
        
        # ต้องใช้ TkinterDnD สำหรับ event เพิ่มเติม แต่ไม่สามารถ bind โดยตรงกับ CustomTkinter widgets ได้
        # ต้อง bind กับ underlying Tkinter widgets
        
        # ดึง underlying widget ของ drop_frame
        # เปลี่ยนจาก binding DragEnter กับ drag_frame
        # เป็นการใช้การเปลี่ยนสีเมื่อมีการ drop แทน
        
        # เพิ่ม event handler สำหรับ drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_file)
        self.image_label.drop_target_register(DND_FILES)
        self.image_label.dnd_bind('<<Drop>>', self.drop_file)
    
    def drop_file(self, event):
        """เมื่อมีการปล่อยไฟล์ลงในพื้นที่รับไฟล์"""
        # แสดงผลลัพธ์การวางไฟล์
        self.drop_frame.configure(fg_color=("lightblue", "darkblue"), border_color=self.primary_color)
        self.after(100, lambda: self.drop_frame.configure(fg_color=("gray90", "gray20"), border_color=("gray80", "gray30")))
        
        # รับเส้นทางไฟล์จาก event
        file_path = event.data
        
        # ทำความสะอาดเส้นทางไฟล์ (ลบเครื่องหมายคำพูดหากมี)
        file_path = file_path.strip('{}')
        file_path = file_path.replace('"', '')
        
        # ตรวจสอบว่าเป็นไฟล์รูปหรือไม่
        file_extension = os.path.splitext(file_path)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        if file_extension in valid_extensions:
            self.image_path = file_path
            self.process_selected_image()
        else:
            self.status_var.set(f"ไฟล์ไม่ใช่รูปภาพที่รองรับ รองรับเฉพาะ {', '.join(valid_extensions)}")

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="เลือกรูปภาพทุเรียน",
            filetypes=[("ไฟล์รูปภาพ", "*.jpg *.png *.jpeg")]
        )
        
        if file_path:
            self.image_path = file_path
            self.process_selected_image()

    def process_selected_image(self):
        """ประมวลผลรูปภาพที่เลือกทั้งจากการคลิกปุ่มหรือลากมาวาง"""
        self.status_var.set(f"กำลังโหลดรูปภาพ: {os.path.basename(self.image_path)}")
        self.update()
        
        # อ่านรูปและเก็บไว้
        img = cv2.imread(self.image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.original_image = img
        
        # ซ่อนปุ่มเลือกรูปเมื่อมีรูปแล้ว
        self.select_btn.place_forget()
        
        # แสดงรูป
        self.update_image_display()
        
        # เคลียร์ผลการวิเคราะห์เดิม
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "กำลังวิเคราะห์รูปภาพ... โปรดรอสักครู่")
        self.result_text.configure(state="disabled")
        
        self.status_var.set(f"กำลังวิเคราะห์: {os.path.basename(self.image_path)}")
        
        # เริ่มการวิเคราะห์อัตโนมัติหลังจากแสดงรูป
        self.after(100, self.analyze_image)  # ทำงานหลังแสดงรูปเสร็จ (100ms)

    def on_frame_configure(self, event):
        # เมื่อ frame มีการเปลี่ยนขนาด ให้แสดงรูปใหม่ถ้ามีรูปอยู่แล้ว
        if self.original_image is not None:
            self.update_image_display()

    def update_image_display(self):
        if self.original_image is None:
            return
        
        # ดึงขนาดของ frame ที่จะแสดงรูป
        frame_width = self.drop_frame.winfo_width()
        frame_height = self.drop_frame.winfo_height()
        
        # ถ้า frame ยังไม่ถูกสร้าง ใช้ค่าเริ่มต้น
        if frame_width <= 1 or frame_height <= 1:
            frame_width = 600
            frame_height = 600
        
        # คำนวณขนาดรูปที่จะแสดง
        img_height, img_width = self.original_image.shape[:2]
        ratio = min((frame_width - 20) / img_width, (frame_height - 20) / img_height)
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        # ปรับขนาดรูป
        try:
            resample_mode = Image.Resampling.LANCZOS
        except AttributeError:
            resample_mode = Image.ANTIALIAS
        
        img_pil = Image.fromarray(self.original_image)
        
        # แก้ไขปัญหา RGBA โดยแปลงเป็น RGB ก่อนใช้งาน
        if img_pil.mode == 'RGBA':
            # สร้างพื้นหลังสีขาวและวางรูป RGBA ทับ
            background = Image.new('RGB', img_pil.size, (255, 255, 255))
            background.paste(img_pil, mask=img_pil.split()[3])  # ใช้ช่อง Alpha เป็น mask
            img_pil = background
        
        try:
            # เพิ่มเอฟเฟกต์ให้รูปภาพ - เพิ่มความคมชัดเล็กน้อย
            img_pil = ImageOps.autocontrast(img_pil, cutoff=0.5)
            img_pil = img_pil.filter(ImageFilter.SHARPEN)
            
            # เพิ่มขอบรูปให้สวยงาม
            img_with_border = ImageOps.expand(img_pil, border=5, fill='white')
        except Exception as e:
            # ถ้าเกิดข้อผิดพลาดในการปรับแต่งรูป ให้ใช้รูปต้นฉบับ
            self.status_var.set(f"ไม่สามารถปรับแต่งรูปภาพ: {str(e)}")
            img_with_border = img_pil
        
        # ปรับขนาด
        img_resized = img_with_border.resize((new_width, new_height), resample_mode)
        
        # สร้าง CTkImage และแสดงผล
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
            img = path_or_array.copy()  # สร้างสำเนาเพื่อป้องกันการเปลี่ยนแปลงข้อมูลต้นฉบับ
            if img is not None:
                if len(img.shape) == 2:  # Grayscale image
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                elif img.shape[2] == 4:  # RGBA image
                    # แยกช่องสัญญาณและใช้เฉพาะ RGB
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif img.shape[2] == 3:  # BGR or RGB image
                    # ตรวจสอบว่าเป็น BGR หรือไม่ (ถ้าจำเป็น)
                    if np.max(img) <= 1.0:  # Normalized image
                        img = (img * 255).astype(np.uint8)
        
        if img is not None:
            self.original_image = img
            self.update_image_display()
        else:
            self.status_var.set("ไม่สามารถโหลดรูปภาพได้")
            # แสดงข้อความในพื้นที่แสดงรูป
            self.image_label.configure(image=None, text="ไม่สามารถโหลดรูปภาพได้")
            # แสดงปุ่มเลือกรูปอีกครั้ง
            self.select_btn.place(relx=0.5, rely=0.5, anchor="center")

    def reset_image_area(self):
        """รีเซ็ตพื้นที่แสดงรูปกลับไปยังสถานะเริ่มต้น"""
        self.image_label.configure(image=None, text="ลากไฟล์รูปมาวางที่นี่ หรือ\nคลิกปุ่มด้านล่างเพื่อเลือกรูปทุเรียน")
        self.select_btn.place(relx=0.5, rely=0.5, anchor="center")

    def analyze_image(self):
        if self.image_path and not self.is_analyzing:
            # ตั้งค่าสถานะกำลังวิเคราะห์เพื่อป้องกันการเรียกซ้ำ
            self.is_analyzing = True
            
            # แสดงสถานะกำลังวิเคราะห์
            self.status_var.set("กำลังวิเคราะห์รูปภาพ... โปรดรอสักครู่")
            self.update()
            
            # วิเคราะห์รูปภาพ
            try:
                img_result, text_result = process_image(self.image_path)
                
                # แสดงผลลัพธ์
                if img_result is not None:
                    self.show_image(img_result)
                
                # แสดงข้อความผลลัพธ์
                self.result_text.configure(state="normal")
                self.result_text.delete("1.0", "end")
                
                # เพิ่มวันที่และเวลาในผลลัพธ์
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
                
                # เปิดใช้งานปุ่มบันทึก
                self.save_btn.configure(state="normal")
                
                self.status_var.set("วิเคราะห์เสร็จสมบูรณ์")
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                
                self.result_text.configure(state="normal")
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", f"เกิดข้อผิดพลาด: {str(e)}\n\nรายละเอียด:\n{error_detail}")
                self.result_text.configure(state="normal")
                self.status_var.set("เกิดข้อผิดพลาดในการวิเคราะห์")
                print(f"Error: {error_detail}")
            
            # ยกเลิกสถานะกำลังวิเคราะห์
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


if __name__ == "__main__":
    app = DurianGraderApp()
    app.mainloop()