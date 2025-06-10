import customtkinter as ctk
from typing import Callable, Dict, Any

class CameraSettingsDialog:
    def __init__(self, parent, current_settings: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("ตั้งค่ากล้อง")
        self.window.geometry("500x750")  # Slightly taller for better spacing
        self.window.transient(parent)
        self.window.grab_set()
        
        # Configure window grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        self.current_settings = current_settings
        self.on_save = on_save
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title label
        title_label = ctk.CTkLabel(
            main_frame, 
            text="ตั้งค่ากล้อง", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Create setting sections
        self._create_batch_settings(main_frame)
        self._create_analysis_settings(main_frame)
        self._create_camera_settings(main_frame)
        
        # Save button at bottom
        self._create_action_buttons(main_frame)
        
    def _create_batch_settings(self, parent):
        """Create batch processing settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # Section header
        header = ctk.CTkLabel(
            section_frame, 
            text="การประมวลผลแบบ Batch", 
            font=ctk.CTkFont(weight="bold")
        )
        header.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Description
        desc = ctk.CTkLabel(
            section_frame,
            text="จำนวนรูปที่จะรวบรวมก่อนการประมวลผลแต่ละครั้ง:",
            font=ctk.CTkFont(size=12)
        )
        desc.pack(anchor="w", padx=10)
        
        # Slider
        self.batch_size_var = ctk.IntVar(value=self.current_settings.get("batch_size", 1))
        batch_slider = ctk.CTkSlider(
            section_frame, 
            from_=1, 
            to=6, 
            number_of_steps=5,
            variable=self.batch_size_var,
            command=self._update_batch_label
        )
        batch_slider.pack(fill="x", padx=10, pady=(5, 0))
        
        # Value display
        self.batch_label = ctk.CTkLabel(
            section_frame, 
            text=f"จำนวนรูป: {self.batch_size_var.get()}",
            font=ctk.CTkFont(size=12)
        )
        self.batch_label.pack(anchor="e", padx=10, pady=(0, 10))
        
    def _create_analysis_settings(self, parent):
        """Create analysis mode settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # Section header
        header = ctk.CTkLabel(
            section_frame, 
            text="โหมดการวิเคราะห์", 
            font=ctk.CTkFont(weight="bold")
        )
        header.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Radio buttons
        self.analysis_mode_var = ctk.StringVar(value=self.current_settings.get("analysis_mode", "auto"))
        
        auto_radio = ctk.CTkRadioButton(
            section_frame, 
            text="วิเคราะห์อัตโนมัติ - ระบบจะทำงานตามช่วงเวลาที่กำหนด", 
            variable=self.analysis_mode_var,
            value="auto",
            font=ctk.CTkFont(size=12)
        )
        auto_radio.pack(anchor="w", padx=20, pady=5)
        
        manual_radio = ctk.CTkRadioButton(
            section_frame, 
            text="วิเคราะห์ด้วยปุ่มกด - ระบบจะทำงานเมื่อผู้ใช้กดปุ่ม", 
            variable=self.analysis_mode_var,
            value="manual",
            font=ctk.CTkFont(size=12)
        )
        manual_radio.pack(anchor="w", padx=20, pady=(5, 10))
        
    def _create_camera_settings(self, parent):
        """Create camera technical settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # Section header
        header = ctk.CTkLabel(
            section_frame, 
            text="การตั้งค่ากล้อง", 
            font=ctk.CTkFont(weight="bold")
        )
        header.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Analysis interval setting
        interval_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        interval_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            interval_frame, 
            text="ความถี่การวิเคราะห์ (วินาที):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10)
        
        self.analysis_interval_var = ctk.DoubleVar(value=self.current_settings.get("analysis_interval", 0.3))
        interval_slider = ctk.CTkSlider(
            interval_frame, 
            from_=0.1, 
            to=2.0, 
            number_of_steps=19,
            variable=self.analysis_interval_var,
            command=self._update_interval_label
        )
        interval_slider.pack(fill="x", padx=10, pady=5)
        
        self.interval_label = ctk.CTkLabel(
            interval_frame, 
            text=f"ความถี่: {self.analysis_interval_var.get():.1f} วินาที",
            font=ctk.CTkFont(size=12)
        )
        self.interval_label.pack(anchor="e", padx=10)
        
        # FPS setting
        fps_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        fps_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(
            fps_frame, 
            text="อัตราเฟรม (FPS):",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10)
        
        self.fps_var = ctk.IntVar(value=self.current_settings.get("fps", 24))
        fps_slider = ctk.CTkSlider(
            fps_frame, 
            from_=1, 
            to=60, 
            number_of_steps=59,
            variable=self.fps_var,
            command=self._update_fps_label
        )
        fps_slider.pack(fill="x", padx=10, pady=5)
        
        self.fps_label = ctk.CTkLabel(
            fps_frame, 
            text=f"FPS: {self.fps_var.get()}",
            font=ctk.CTkFont(size=12)
        )
        self.fps_label.pack(anchor="e", padx=10, pady=(0, 10))
        
    def _create_action_buttons(self, parent):
        """Create action buttons at bottom"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame, 
            text="บันทึกการตั้งค่า", 
            command=self._save_settings,
            height=40,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(weight="bold")
        )
        save_btn.pack(side="right", padx=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame, 
            text="ยกเลิก", 
            command=self.window.destroy,
            height=40,
            fg_color="#616161",
            hover_color="#424242",
            font=ctk.CTkFont(weight="bold")
        )
        cancel_btn.pack(side="right")
        
    def _update_batch_label(self, value):
        self.batch_label.configure(text=f"จำนวนรูป: {int(value)}")
        
    def _update_interval_label(self, value):
        self.interval_label.configure(text=f"ความถี่: {value:.1f} วินาที")
        
    def _update_fps_label(self, value):
        self.fps_label.configure(text=f"FPS: {int(value)}")
        
    def _save_settings(self):
        settings = {
            "batch_size": self.batch_size_var.get(),
            "analysis_mode": self.analysis_mode_var.get(),
            "analysis_interval": self.analysis_interval_var.get(),
            "fps": self.fps_var.get()
        }
        try:
            self.on_save(settings)
        except AttributeError as e:
            print(f"Warning: Callback function failed - {str(e)}")
        finally:
            self.window.destroy()