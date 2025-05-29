import customtkinter as ctk
from customtkinter import CTkImage
import tkinterdnd2
from tkinterdnd2 import TkinterDnD
from tkinter import filedialog
import cv2
from PIL import Image
from datetime import datetime
import pathlib

from utils.durian_grader import process_multi_view
from utils.camera_manager import CameraManager
from utils.image_combiner import combine_images_grid

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

def resize_with_aspect_ratio(image, max_width, max_height):
    img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    img_pil.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return img_pil

class DurianGraderApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Durian Grading System - Multi View")
        self.geometry("1440x960")
        self.minsize(1200, 800)

        self.camera_ids = [0, 1, 2, 3, 4, 5]
        self.camera_manager = CameraManager(self.camera_ids)
        self.camera_manager.initialize_cameras()
        self.frames = [None] * 6
        self.loaded_images = {}
        self.analysis_results = [None] * 6  #เก็บภาพหลังวิเคราะห์สำหรับแต่ละ view

        # --- Main container ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color="#4CAF50")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=2)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # --- Preview area (left) ---
        self.preview_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.preview_frame.grid_rowconfigure((0,1), weight=1)
        self.preview_frame.grid_columnconfigure((0,1,2), weight=1)

        self.image_labels = []
        for i in range(6):
            label = ctk.CTkLabel(
                self.preview_frame, 
                text=f"View {i+1}", 
                width=320, height=240, 
                fg_color="#111111",
                corner_radius=10,
                font=ctk.CTkFont(size=14, weight="bold"),
                justify="center"
            )
            label.grid(row=i//3, column=i%3, padx=15, pady=15, sticky="nsew")
            self.image_labels.append(label)

            # Enable drag & drop on each label
            label.drop_target_register(tkinterdnd2.DND_FILES)
            label.dnd_bind('<<Drop>>', lambda e, idx=i: self.on_drop_file(e, idx))

            # Bind click to open file dialog
            label.bind("<Button-1>", lambda e, idx=i: self.open_file_dialog(idx))

        # --- Right side frame (Result + Buttons) ---
        self.right_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_frame.grid_rowconfigure(0, weight=3)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Result textbox
        self.result_textbox = ctk.CTkTextbox(
            self.right_frame,
            font=ctk.CTkFont(size=14),
            corner_radius=10,
            border_width=2,
            border_color="#4CAF50",
            fg_color="#111111",
            text_color="white",
            wrap="word",
            state="disabled"
        )
        self.result_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.result_textbox.configure(state="disabled")

        # Buttons frame
        self.button_frame = ctk.CTkFrame(self.right_frame)
        self.button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.button_frame.grid_columnconfigure((0,1), weight=1)

        self.analyze_button = ctk.CTkButton(
            self.button_frame, 
            text="📷 วิเคราะห์", 
            command=self.capture_and_analyze, 
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.analyze_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.save_button = ctk.CTkButton(
            self.button_frame, 
            text="💾 บันทึก", 
            command=self.save_combined_image,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.save_button.grid(row=0, column=1, sticky="ew")

        self.after(1000, self.update_previews)

    def update_previews(self):
        frames = self.camera_manager.get_frames()

        for i in range(6):
            if self.analysis_results[i] is not None:
                frame = self.analysis_results[i]
            elif i in self.loaded_images:
                frame = self.loaded_images[i]
            else:
                frame = frames[i] if frames else None

            if frame is not None:
                self.frames[i] = frame
                self.update_single_preview(i, frame)
            else:
                self.image_labels[i].configure(text=f"View {i+1}\n(ไม่สามารถแสดงภาพได้)", image=None)

        self.after(1000, self.update_previews)

    def update_single_preview(self, index, frame):
        label = self.image_labels[index]

        # รอให้ label ได้ขนาดจริงก่อน
        label.update_idletasks()

        max_width = label.winfo_width() - 20
        max_height = label.winfo_height() - 20

        # ป้องกันกรณี max_width/height <= 0
        if max_width <= 0:
            max_width = 300
        if max_height <= 0:
            max_height = 200

        img_pil = resize_with_aspect_ratio(frame, max_width, max_height)
        img_ctk = CTkImage(light_image=img_pil, dark_image=img_pil, size=img_pil.size)
        label.configure(image=img_ctk, text="")
        label.image = img_ctk

    def on_drop_file(self, event, index):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]

        if pathlib.Path(file_path).suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            img = cv2.imread(file_path)
            if img is not None:
                self.loaded_images[index] = img
                self.frames[index] = img
                self.analysis_results[index] = None  # ล้างภาพวิเคราะห์เดิม
                self.update_single_preview(index, img)

    def open_file_dialog(self, index):
        file_path = filedialog.askopenfilename(
            title=f"เลือกไฟล์รูปสำหรับกล้อง View {index+1}",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                self.loaded_images[index] = img
                self.frames[index] = img
                self.analysis_results[index] = None  # ล้างภาพวิเคราะห์เดิม
                self.update_single_preview(index, img)

    def capture_and_analyze(self):
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", "กำลังวิเคราะห์ภาพจากกล้อง...\n")
        self.update()

        captured_frames = self.frames

        # เรียกใช้งาน process_multi_view ซึ่งคืนค่า (frames_with_results, result_text)
        frames_with_results, result_text = process_multi_view(captured_frames)

        # เก็บภาพผลวิเคราะห์แต่ละ view ลง self.analysis_results
        if frames_with_results is not None and len(frames_with_results) == 6:
            self.analysis_results = frames_with_results

        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", f"📅 วิเคราะห์เมื่อ: {current_time}\n\n{result_text}")
        self.result_textbox.configure(state="disabled")

        # อัพเดต preview ให้แสดงภาพผลวิเคราะห์ทันที
        for i, frame in enumerate(self.analysis_results):
            if frame is not None:
                self.update_single_preview(i, frame)

    def save_combined_image(self):
        frames = self.analysis_results if any(self.analysis_results) else self.frames
        combined_image = combine_images_grid(frames, grid_size=(2, 3), image_size=(320, 240))

        now = datetime.now()
        default_filename = now.strftime("%Y%m%d-%H%M%S") + "-combined_image.jpg"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG Image", "*.jpg"), ("PNG Image", "*.png")],
            initialfile=default_filename,
            title="บันทึก"
        )

        if file_path:
            cv2.imwrite(file_path, combined_image)

    def on_closing(self):
        self.camera_manager.release_cameras()
        self.destroy()

if __name__ == "__main__":
    app = DurianGraderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
