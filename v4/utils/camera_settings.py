import customtkinter as ctk
from typing import Callable, Dict, Any

class CameraSettingsDialog:
    def __init__(self, parent, current_settings: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("ตั้งค่ากล้อง")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.current_settings = current_settings
        self.on_save = on_save
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="ตั้งค่ากล้องและการประมวลผล", 
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Batch size settings
        batch_frame = ctk.CTkFrame(main_frame)
        batch_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(batch_frame, text="จำนวนรูปในการประมวลผลแบบ Batch:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.batch_size_var = ctk.IntVar(value=self.current_settings.get("batch_size", 1))
        batch_slider = ctk.CTkSlider(
            batch_frame, 
            from_=1, 
            to=6, 
            number_of_steps=5,
            variable=self.batch_size_var,
            command=self._update_batch_label
        )
        batch_slider.pack(fill="x", padx=10, pady=5)
        
        self.batch_label = ctk.CTkLabel(batch_frame, text=f"จำนวนรูป: {self.batch_size_var.get()}")
        self.batch_label.pack(anchor="e", padx=10, pady=(0, 10))
        
        # Analysis mode settings
        analysis_frame = ctk.CTkFrame(main_frame)
        analysis_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(analysis_frame, text="โหมดการวิเคราะห์:").pack(anchor="w", padx=10, pady=(10, 5))
        
        self.analysis_mode_var = ctk.StringVar(value=self.current_settings.get("analysis_mode", "auto"))
        
        auto_radio = ctk.CTkRadioButton(
            analysis_frame, 
            text="วิเคราะห์อัตโนมัติ", 
            variable=self.analysis_mode_var,
            value="auto"
        )
        auto_radio.pack(anchor="w", padx=20, pady=5)
        
        manual_radio = ctk.CTkRadioButton(
            analysis_frame, 
            text="วิเคราะห์ด้วยปุ่มกด", 
            variable=self.analysis_mode_var,
            value="manual"
        )
        manual_radio.pack(anchor="w", padx=20, pady=5)
        
        # Camera settings
        camera_frame = ctk.CTkFrame(main_frame)
        camera_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(camera_frame, text="ความถี่การวิเคราะห์ (วินาที):").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.analysis_interval_var = ctk.DoubleVar(value=self.current_settings.get("analysis_interval", 0.3))
        interval_slider = ctk.CTkSlider(
            camera_frame, 
            from_=0.1, 
            to=2.0, 
            number_of_steps=19,
            variable=self.analysis_interval_var,
            command=self._update_interval_label
        )
        interval_slider.pack(fill="x", padx=10, pady=5)
        
        self.interval_label = ctk.CTkLabel(camera_frame, text=f"ความถี่: {self.analysis_interval_var.get():.1f} วินาที")
        self.interval_label.pack(anchor="e", padx=10, pady=(0, 10))
        
        # Save button
        save_btn = ctk.CTkButton(
            main_frame, 
            text="บันทึกการตั้งค่า", 
            command=self._save_settings,
            height=40,
            fg_color="#4CAF50",
            hover_color="#689F38"
        )
        save_btn.pack(pady=20)
        
    def _update_batch_label(self, value):
        self.batch_label.configure(text=f"จำนวนรูป: {int(value)}")
        
    def _update_interval_label(self, value):
        self.interval_label.configure(text=f"ความถี่: {value:.1f} วินาที")
        
    def _save_settings(self):
        settings = {
            "batch_size": self.batch_size_var.get(),
            "analysis_mode": self.analysis_mode_var.get(),
            "analysis_interval": self.analysis_interval_var.get()
        }
        self.on_save(settings)
        self.window.destroy()
