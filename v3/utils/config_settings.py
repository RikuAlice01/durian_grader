import customtkinter as ctk
from typing import Callable, Dict, Any

class ConfigSettingsDialog:
    def __init__(self, parent, current_settings: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("ตั้งค่าการแสดงผล")
        self.window.geometry("500x600")
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
            text="ตั้งค่าการแสดงผล", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Create setting sections
        self._create_rendering_settings(main_frame)
        self._create_grading_settings(main_frame)
        
        # Save button at bottom
        self._create_action_buttons(main_frame)
        
    def _create_rendering_settings(self, parent):
        """Create rendering settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # Section header
        header = ctk.CTkLabel(
            section_frame, 
            text="การแสดงผล", 
            font=ctk.CTkFont(weight="bold")
        )
        header.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Line thickness
        self.line_thickness_var = self._create_numeric_entry(
            section_frame, 
            "Rendering", 
            "line_thickness", 
            "ความหนาเส้นขอบ:", 
            row=0
        )
        
        # Text size
        self.text_size_var = self._create_numeric_entry(
            section_frame,
            "Rendering",
            "text_size",
            "ขนาดตัวอักษร:",
            row=1
        )
        
        # Text bold
        self.text_bold_var = self._create_numeric_entry(
            section_frame,
            "Rendering",
            "text_bold",
            "ความหนาอักษร:",
            row=2
        )
        
        # Point size
        self.point_size_var = self._create_numeric_entry(
            section_frame,
            "Rendering",
            "point_size",
            "ขนาดจุด:",
            row=3
        )
        
    def _create_grading_settings(self, parent):
        """Create grading settings section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # Section header
        header = ctk.CTkLabel(
            section_frame, 
            text="การให้คะแนน", 
            font=ctk.CTkFont(weight="bold")
        )
        header.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Distance threshold
        self.distance_threshold_var = self._create_numeric_entry(
            section_frame,
            "Grading",
            "distance_threshold",
            "ค่าเกณฑ์ระยะห่าง:",
            row=0
        )
        
        # Percentage grading
        self.percentage_grading_var = self._create_numeric_entry(
            section_frame,
            "Grading",
            "percentage_grading",
            "ค่าเกณฑ์เปอร์เซ็นต์ (%):",
            row=1
        )
        
        # Adjustment value
        self.adj_var = self._create_numeric_entry(
            section_frame,
            "Grading",
            "adj",
            "ค่าความลึกการตรวจ:",
            row=2
        )
        
    def _create_numeric_entry(self, parent, section, key, label_text, row):
        """Helper to create numeric entry fields"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame, text=label_text).pack(side="left", padx=(0, 10))

        var = ctk.StringVar()
        if section in self.current_settings and key in self.current_settings[section]:
            var.set(self.current_settings[section][key])

        entry = ctk.CTkEntry(frame, textvariable=var, width=80)
        entry.pack(side="right")

        return var
        
    def _create_action_buttons(self, parent):
        """Create action buttons at bottom"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
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
        
    def _save_settings(self):
        """Collect all settings and pass to callback"""
        settings = {
            "Rendering": {
                "line_thickness": self.line_thickness_var.get(),
                "text_size": self.text_size_var.get(),
                "text_bold": self.text_bold_var.get(),
                "point_size": self.point_size_var.get()
            },
            "Grading": {
                "distance_threshold": self.distance_threshold_var.get(),
                "percentage_grading": self.percentage_grading_var.get(),
                "adj": self.adj_var.get()
            }
        }
        
        try:
            self.on_save(settings)
        except Exception as e:
            print(f"Error saving config: {e}")
        finally:
            self.window.destroy()