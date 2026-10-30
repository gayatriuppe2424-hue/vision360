"""
Vision360 - Next-Gen Hands-Free Accessibility & Digital Wellness Platform
========================================================================
UI Shell: Obsidian Studio Neo-Glass (CustomTkinter + Native Smooth Canvas)
Architecture: Left Sidebar Rail Navigation + Dedicated EyeRest Target Mockup View
Engine: Dwell-Clicking, Smart Zone Scroll, Mouth Emergency Brake, Virtual Keyboard,
        Blink-Rate Monitor (BPM), 3D Posture Guardian, Figure-8 Eye Gymnastics,
        Daily Wellness Rings, and Achievement Badges.
100% of background OpenCV, MediaPipe, threading, PyAutoGUI and state logic preserved.
"""

import tkinter as tk
import customtkinter as ctk
import time
import math
import json
import os
import sys
import platform
import datetime
import threading
import queue
import collections
import numpy as np
import cv2
import mediapipe as mp
import pyautogui
import ctypes
from pathlib import Path
try:
    from PIL import Image, ImageTk
except ImportError:
    Image, ImageTk = None, None

# ──────────────────────────────────────────────────────────────────────────────
#  Path helpers (work from source AND when packaged with PyInstaller)
# ──────────────────────────────────────────────────────────────────────────────
def resource_path(*parts):
    """Read-only bundled files (model, images, gif)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return Path(base, *parts)

def user_data_dir():
    """Writable per-user folder for profiles (APPDATA on Windows)."""
    if platform.system() == "Windows":
        root = os.environ.get("APPDATA") or str(Path.home())
    elif platform.system() == "Darwin":
        root = str(Path.home() / "Library" / "Application Support")
    else:
        root = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    d = Path(root) / "Vision360"
    d.mkdir(parents=True, exist_ok=True)
    return d

# ──────────────────────────────────────────────────────────────────────────────
#  Global Theme & Colors (Matching Target Mockup)
# ──────────────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG_VOID         = "#080C16"   # Deepest obsidian canvas
BG_SIDEBAR      = "#090D18"   # Left navigation rail
BG_MAIN         = "#0B111E"   # Deep navy-obsidian background
BG_HEADER       = "#0D1527"   # Header bar background
BG_CARD         = "#0F1A2E"   # Primary glass cards
BG_CARD_INNER   = "#13213B"   # Elevated card section
BG_PILL         = "#152442"   # Pill container background
BG_PILL_ACTIVE  = "#1E355F"   # Active pill highlight
BG_SURFACE      = "#18243D"   # Interactive surfaces / hover
BG_ELEVATED     = "#1E355F"   # Active sidebar & elevated container highlight

BORDER_CARD     = "#1D2E4E"   # Crisp card border
BORDER_SUBTLE   = "#1A253B"   # 1px structural borders
BORDER_GLOW     = "#243656"   # Active luminous highlights

ACCENT_CYAN     = "#38BDF8"   # Bright Neon Sky Cyan
ACCENT_BLUE     = "#60A5FA"   # Electric Soft Blue
ACCENT_PURPLE   = "#A855F7"   # Bright Arcade Violet (XP / Badges)
ACCENT_GREEN    = "#10B981"   # Bio-Emerald (Optimal / Healthy)
ACCENT_AMBER    = "#F59E0B"   # Luminous Amber (Guideline / Caution)
ACCENT_GOLD     = "#FBBF24"   # Achievement Gold
ACCENT_RED      = "#F43F5E"   # Rose Coral (Fatigue / Turtle Neck Alert)

TEXT_PRIMARY    = "#F8FAFC"   # Crisp White
TEXT_SECONDARY  = "#94A3B8"   # Slate Text
TEXT_MUTED      = "#94A3B8"   # Raised Muted Text for high readability

CORNER_RADIUS   = 16

# Blink-rate measurement: 60-second window, reporting only after 30 seconds face time
BPM_WINDOW      = 60.0
BPM_MIN_WINDOW  = 30.0


def _safe_num(src, key, default, lo=None, hi=None):
    """Read a number from a (possibly corrupt) JSON dict, clamped to [lo, hi]."""
    try:
        x = float(src.get(key, default))
        if x != x or x in (float("inf"), float("-inf")):
            raise ValueError
    except Exception:
        x = float(default)
    if lo is not None: x = max(lo, x)
    if hi is not None: x = min(hi, x)
    return x


def _parse_date(s):
    try:
        return datetime.date.fromisoformat(str(s))
    except Exception:
        return None

# Expanded Autocomplete Dictionary for Virtual Keyboard
COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at", 
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would", "there", 
    "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", 
    "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them", "see", "other", "than", "then", 
    "now", "look", "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", 
    "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us", "are", "is", "was", "were", "been", "has", 
    "had", "doing", "did", "does", "am", "youtube", "google", "gmail", "facebook", "python", "vision", "hello", "world", "search",
    "com", "please", "help", "open", "close", "yes", "thanks", "where", "much", "very", "many", "before", "same", "right", "why", 
    "tell", "ask", "show", "try", "call", "keep", "feel", "leave", "put", "bring", "let", "begin", "seem", "talk", "turn", "start"
]

# ══════════════════════════════════════════════════════════════════════════════
#  Virtual Keyboard
# ══════════════════════════════════════════════════════════════════════════════
class VirtualKeyboard(ctk.CTkToplevel):
    def __init__(self, master, close_callback):
        super().__init__(master)
        self.close_callback = close_callback
        self.attributes('-topmost', True)
        self.overrideredirect(True) 
        self.configure(fg_color=BG_CARD)
        self.attributes("-alpha", 0.96) 
        
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x08000000) 
        except: pass

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        kb_w = min(840, sw - 40) 
        kb_h = 260               
        x_pos = (sw - kb_w) // 2 
        y_pos = sh - kb_h - 110  
        self.geometry(f"{kb_w}x{kb_h}+{x_pos}+{y_pos}")

        self.current_word = ""
        self.suggestion_btns = []
        self.key_btns = []
        self.shift_active = False
        self.num_active = False
        
        for i in range(20): self.grid_columnconfigure(i, weight=1)
        for i in range(5): self.grid_rowconfigure(i, weight=1 if i==0 else 2)
        self._build_ui()

    def _build_ui(self):
        for i in range(4):
            btn = ctk.CTkButton(self, text="", fg_color=BG_CARD_INNER, text_color=ACCENT_CYAN, font=ctk.CTkFont(size=13, weight="bold"))
            btn.grid(row=0, column=i*5, columnspan=5, sticky="nsew", padx=2, pady=(6, 2))
            self.suggestion_btns.append(btn)
        self._render_keys()

    def _render_keys(self):
        for btn in self.key_btns: btn.destroy()
        self.key_btns.clear()

        if self.num_active:
            keys = [
                ("1",1,0,2), ("2",1,2,2), ("3",1,4,2), ("4",1,6,2), ("5",1,8,2), ("6",1,10,2), ("7",1,12,2), ("8",1,14,2), ("9",1,16,2), ("0",1,18,2),
                ("@",2,1,2), ("#",2,3,2), ("$",2,5,2), ("_",2,7,2), ("&",2,9,2), ("-",2,11,2), ("+",2,13,2), ("(",2,15,2), (")",2,17,2),
                ("*",3,0,3), ('"',3,3,2), ("'",3,5,2), (":",3,7,2), (";",3,9,2), ("!",3,11,2), ("?",3,13,2), ("/",3,15,2), ("⌫",3,17,3),
                ("ABC",4,0,3), (",",4,3,2), ("SPACE",4,5,8), (".",4,13,2), ("ENTER",4,15,3), ("✖",4,18,2)
            ]
        else:
            keys = [
                ("q",1,0,2), ("w",1,2,2), ("e",1,4,2), ("r",1,6,2), ("t",1,8,2), ("y",1,10,2), ("u",1,12,2), ("i",1,14,2), ("o",1,16,2), ("p",1,18,2),
                ("a",2,1,2), ("s",2,3,2), ("d",2,5,2), ("f",2,7,2), ("g",2,9,2), ("h",2,11,2), ("j",2,13,2), ("k",2,15,2), ("l",2,17,2),
                ("⇧",3,0,3), ("z",3,3,2), ("x",3,5,2), ("c",3,7,2), ("v",3,9,2), ("b",3,11,2), ("n",3,13,2), ("m",3,15,2), ("⌫",3,17,3),
                ("?123",4,0,3), (",",4,3,2), ("SPACE",4,5,8), (".",4,13,2), ("ENTER",4,15,3), ("✖",4,18,2)
            ]

        for (key, r, c, span) in keys:
            display_text = key.upper() if (self.shift_active and len(key)==1 and key.isalpha()) else key
            fg = BG_CARD_INNER
            text_color = TEXT_PRIMARY
            hover = BORDER_CARD
            weight = "normal" if len(key)==1 else "bold"
            if key == "SPACE": fg, hover = ACCENT_CYAN, ACCENT_BLUE
            elif key in ["ENTER", "⌫", "⇧", "?123", "ABC", "✖"]: fg, hover = BG_PILL, BORDER_CARD
            if key == "⇧" and self.shift_active: fg = ACCENT_CYAN

            btn = ctk.CTkButton(self, text=display_text, font=ctk.CTkFont(size=14, weight=weight),
                                fg_color=fg, text_color=text_color, hover_color=hover,
                                command=lambda k=key: self.handle_key(k))
            btn.grid(row=r, column=c, columnspan=span, sticky="nsew", padx=2, pady=2)
            self.key_btns.append(btn)

    def handle_key(self, key):
        if key == "⇧":
            self.shift_active = not self.shift_active
            self._render_keys()
            return
        elif key == "?123":
            self.num_active = True
            self.shift_active = False
            self._render_keys()
            return
        elif key == "ABC":
            self.num_active = False
            self._render_keys()
            return
        elif key == "SPACE":
            pyautogui.press('space')
            self.current_word = ""
            self.update_suggestions()
            return
        elif key == "⌫":
            pyautogui.press('backspace')
            if len(self.current_word) > 0: self.current_word = self.current_word[:-1]
            self.update_suggestions()
            return
        elif key == "ENTER":
            pyautogui.press('enter')
            self.current_word = ""
            self.update_suggestions()
            return
        elif key == "✖":
            self.close_callback()
            return
        
        char = key.upper() if self.shift_active else key
        pyautogui.write(char)
        if self.shift_active:
            self.shift_active = False
            self._render_keys()
        if char in [",", ".", "?", "!", "@", '"', "'", "(", ")"]: self.current_word = ""
        else: self.current_word += char
        self.update_suggestions()
        
    def _bind_suggestion(self, btn, word):
        btn.configure(text=word.upper(), command=lambda w=word: self.apply_suggestion(w))

    def apply_suggestion(self, word):
        remaining_chars = word[len(self.current_word):]
        if remaining_chars: pyautogui.write(remaining_chars)
        pyautogui.press('space')
        self.current_word = ""
        self.update_suggestions()

    def update_suggestions(self):
        if not self.current_word:
            for btn in self.suggestion_btns: btn.configure(text="", command=lambda: None)
            return
        matches = [w for w in COMMON_WORDS if w.startswith(self.current_word.lower())][:4]
        for i, btn in enumerate(self.suggestion_btns):
            if i < len(matches): self._bind_suggestion(btn, matches[i])
            else: btn.configure(text="", command=lambda: None)

# ══════════════════════════════════════════════════════════════════════════════
#  Global Posture Alert Overlay (Visible outside the app)
# ══════════════════════════════════════════════════════════════════════════════
class GlobalPostureAlert(ctk.CTkToplevel):
    def __init__(self, master, dist, is_critical):
        super().__init__(master)
        
        self.attributes('-topmost', True)
        self.overrideredirect(True) 
        self.attributes("-alpha", 0.90)  
        self.configure(fg_color=BG_VOID)

        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x08000000) 
        except: pass

        w, h = 340, 50
        sw = self.winfo_screenwidth()
        self.geometry(f"{w}x{h}+{int((sw - w) / 2)}+30") 

        # Empty container that we will color dynamically
        self.border = ctk.CTkFrame(self, fg_color=BG_CARD, border_width=2, corner_radius=12)
        self.border.pack(fill="both", expand=True)
        
        self.lbl = ctk.CTkLabel(self.border, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl.pack(expand=True)

        self.update_dist(dist, is_critical)

    def update_dist(self, dist, is_critical):
        """Updates the text and color dynamically based on severity."""
        if is_critical:
            color = ACCENT_RED
            msg = f"⚠️ TURTLE NECK ({int(dist)} cm) - Straighten Spine!"
        else:
            color = ACCENT_AMBER
            msg = f"👀 Leaning in ({int(dist)} cm) - Mind your posture"
            
        self.border.configure(border_color=color)
        self.lbl.configure(text=msg, text_color=color)
# ══════════════════════════════════════════════════════════════════════════════
#  20-20-20 Break Gatekeeper Notification (With Animated GIF & Global Override)
# ══════════════════════════════════════════════════════════════════════════════
class BreakGatekeeper(ctk.CTkToplevel):
    def __init__(self, master, break_duration=20, on_close=None):
        super().__init__(master)
        self.on_close = on_close
        
        # Make it always on top and borderless
        self.attributes('-topmost', True)
        self.overrideredirect(True) 
        self.attributes("-alpha", 0.95)
        self.configure(fg_color=BG_VOID)

        # --- THE MAGIC WINDOWS FIX ---
        # This detaches the popup from the main app so it shows up even if the app is minimized,
        # and prevents it from stealing your typing focus (like if you are in Word/Chrome).
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x08000000) 
        except: pass
        
        # Force the window to physically lift above all other OS windows
        self.lift()
        # -----------------------------

        # Center firmly on the screen
        w, h = 420, 340 
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{int((sw - w) / 2)}+{int((sh - h) / 2)}")

        # Glowing border card
        self.border = ctk.CTkFrame(self, fg_color=BG_CARD, border_width=2, border_color=ACCENT_CYAN, corner_radius=16)
        self.border.pack(fill="both", expand=True, padx=4, pady=4)
        
        # --- GIF Loading & Display ---
        self.gif_lbl = ctk.CTkLabel(self.border, text="")
        self.gif_lbl.pack(pady=(15, 5))
        
        self.frames = []
        self.current_frame = 0
        self._load_gif()
        
        ctk.CTkLabel(self.border, text="👁️ TIME FOR A BREAK", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_CYAN).pack(pady=(0, 5))
        ctk.CTkLabel(self.border, text="Look at something 20 feet away to rest your eyes.", font=ctk.CTkFont(size=13), text_color=TEXT_PRIMARY).pack()
        
        self.time_lbl = ctk.CTkLabel(self.border, text=f"{break_duration}s", font=ctk.CTkFont(size=36, weight="bold"), text_color=ACCENT_GREEN)
        self.time_lbl.pack(pady=(10, 15))

        self.remaining = break_duration
        self.countdown()

    def _load_gif(self):
        """Loads the cat_gatekeeper GIF robustly using native frame seeking."""
        try:
            base_dir = resource_path()
            
            # Check for multiple possible extensions/names
            possible_names = ["cat_gatekeeper.gif", "cat_gatekeeper"]
            gif_path = None
            
            for name in possible_names:
                temp_path = base_dir / name
                if temp_path.exists():
                    gif_path = temp_path
                    break
            
            if gif_path:
                img = Image.open(str(gif_path))
                
                # Robust frame extraction (No extra imports needed)
                for i in range(getattr(img, 'n_frames', 1)):
                    img.seek(i)
                    # Convert to RGBA and resize cleanly
                    frame_rgba = img.convert("RGBA").resize((160, 160), Image.Resampling.LANCZOS)
                    ctk_frame = ctk.CTkImage(light_image=frame_rgba, dark_image=frame_rgba, size=(160, 160))
                    self.frames.append(ctk_frame)
                
                if self.frames:
                    self._animate_gif()
            else:
                self.gif_lbl.configure(text="[GIF File Not Found]", text_color=TEXT_MUTED)
                
        except Exception as e:
            error_msg = str(e)
            self.gif_lbl.configure(text=f"[Error: {error_msg[:20]}]", text_color=TEXT_MUTED)
            print(f"GIF Load Error: {e}")

    def _animate_gif(self):
        """Loops through the loaded GIF frames."""
        if self.frames:
            self.gif_lbl.configure(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            # 180ms delay for a relaxed, slow cat animation
            self.after(180, self._animate_gif)

    def countdown(self):
        if self.remaining > 0:
            self.time_lbl.configure(text=f"{self.remaining}s")
            self.remaining -= 1
            self.after(1000, self.countdown)
        else:
            if self.on_close:
                self.on_close()
            self.destroy()

    def _load_gif(self):
        """Loads the cat_gatekeeper GIF robustly using native frame seeking."""
        try:
            base_dir = resource_path()
            
            # Check for multiple possible extensions/names
            possible_names = ["cat_gatekeeper.gif", "cat_gatekeeper"]
            gif_path = None
            
            for name in possible_names:
                temp_path = base_dir / name
                if temp_path.exists():
                    gif_path = temp_path
                    break
            
            if gif_path:
                img = Image.open(str(gif_path))
                
                # Robust frame extraction (No extra imports needed)
                for i in range(getattr(img, 'n_frames', 1)):
                    img.seek(i)
                    # Convert to RGBA and resize cleanly
                    frame_rgba = img.convert("RGBA").resize((160, 160), Image.Resampling.LANCZOS)
                    ctk_frame = ctk.CTkImage(light_image=frame_rgba, dark_image=frame_rgba, size=(160, 160))
                    self.frames.append(ctk_frame)
                
                if self.frames:
                    self._animate_gif()
            else:
                self.gif_lbl.configure(text="[GIF File Not Found]", text_color=TEXT_MUTED)
                
        except Exception as e:
            # If it fails, print the actual Python error on the screen so we can see it!
            error_msg = str(e)
            self.gif_lbl.configure(text=f"[Error: {error_msg[:20]}]", text_color=TEXT_MUTED)
            print(f"GIF Load Error: {e}")

    def _animate_gif(self):
        """Loops through the loaded GIF frames."""
        if self.frames:
            self.gif_lbl.configure(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            # CHANGE THE NUMBER HERE to slow it down (e.g., 100 or 120)
            self.after(200, self._animate_gif)

    def countdown(self):
        if self.remaining > 0:
            self.time_lbl.configure(text=f"{self.remaining}s")
            self.remaining -= 1
            self.after(1000, self.countdown)
        else:
            if self.on_close:
                self.on_close()
            self.destroy()

# ══════════════════════════════════════════════════════════════════════════════
#  Floating Dock
# ══════════════════════════════════════════════════════════════════════════════
class FloatingDock(ctk.CTkToplevel):
    def __init__(self, master, click_mode_var):
        super().__init__(master)
        self.click_mode_var = click_mode_var
        self.attributes('-topmost', True)
        self.overrideredirect(True) 
        self.configure(fg_color=BG_CARD)
        self.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.btn_left   = self._create_mode_btn("Left", 0)
        self.btn_right  = self._create_mode_btn("Right", 1)
        self.btn_double = self._create_mode_btn("Double", 2)
        self.btn_drag   = self._create_mode_btn("Drag", 3)
        self.btn_scroll = self._create_mode_btn("Scroll", 4)
        self.btn_type   = self._create_mode_btn("Type", 5)
        self.update_styles()
        self.lift()

    def _create_mode_btn(self, mode_name, col):
        btn = ctk.CTkButton(
            self, text=mode_name, font=ctk.CTkFont(size=11, weight="bold"),
            height=32, fg_color=BG_CARD_INNER, hover_color=BORDER_CARD,
            text_color=TEXT_SECONDARY, command=lambda: self.set_mode(mode_name)
        )
        btn.grid(row=0, column=col, padx=4, pady=8, sticky="ew")
        return btn

    def set_mode(self, mode_name):
        if self.click_mode_var.get() == mode_name and mode_name != "Left":
            self.click_mode_var.set("Left")
        else:
            self.click_mode_var.set(mode_name)
        self.update_styles()

    def update_styles(self):
        current = self.click_mode_var.get()
        buttons = {
            "Left": self.btn_left, "Right": self.btn_right, 
            "Double": self.btn_double, "Drag": self.btn_drag, 
            "Scroll": self.btn_scroll, "Type": self.btn_type
        }
        for name, btn in buttons.items():
            if name == current:
                btn.configure(fg_color=ACCENT_CYAN, text_color=BG_MAIN)
            else:
                btn.configure(fg_color=BG_CARD_INNER, text_color=TEXT_SECONDARY)


# ══════════════════════════════════════════════════════════════════════════════
#  Profile Switcher Dialog (Multi-User Workstation Support)
# ══════════════════════════════════════════════════════════════════════════════
class ProfileSwitcherDialog(ctk.CTkToplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Vision360 // Profile Switcher")
        self.geometry("540x580")
        self.minsize(500, 480)
        self.configure(fg_color=BG_VOID)
        self.attributes('-topmost', True)
        
        try:
            self.update_idletasks()
            mx = master.winfo_rootx() + (master.winfo_width() - 540) // 2
            my = master.winfo_rooty() + (master.winfo_height() - 580) // 2
            self.geometry(f"+{max(20, mx)}+{max(20, my)}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        header.pack(fill="x", padx=0, pady=(0, 14))
        
        top_h = ctk.CTkFrame(header, fg_color="transparent")
        top_h.pack(fill="x", padx=20, pady=16)
        
        title_box = ctk.CTkFrame(top_h, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(title_box, text="👥 WORKSTATION PROFILES", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(title_box, text="Switch users or create a new profile for this computer",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        close_btn = ctk.CTkButton(top_h, text="✕", width=28, height=28, corner_radius=14,
                                  fg_color=BG_CARD_INNER, hover_color=BORDER_CARD,
                                  text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold"),
                                  command=self.destroy)
        close_btn.pack(side="right")

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Bottom Action Bar
        btn_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        btn_bar.pack(fill="x", side="bottom")
        
        row = ctk.CTkFrame(btn_bar, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=14)
        
        ctk.CTkButton(row, text="+ New Profile", width=120, height=34, corner_radius=8,
                      font=ctk.CTkFont(size=11, weight="bold"), fg_color=ACCENT_CYAN,
                      hover_color=ACCENT_BLUE, text_color=BG_MAIN,
                      command=self._on_add_new).pack(side="left", padx=(0, 8))

        ctk.CTkButton(row, text="👤 Guest Mode", width=110, height=34, corner_radius=8,
                      font=ctk.CTkFont(size=11, weight="bold"), fg_color=BG_CARD_INNER,
                      hover_color=BORDER_GLOW, text_color=TEXT_PRIMARY,
                      command=self._on_guest).pack(side="left", padx=(0, 8))

        ctk.CTkButton(row, text="Done", width=80, height=34, corner_radius=8,
                      font=ctk.CTkFont(size=11, weight="bold"), fg_color=BG_CARD_INNER,
                      hover_color=BORDER_CARD, text_color=TEXT_SECONDARY,
                      command=self.destroy).pack(side="right")

        self._render_profiles_list()

    def _render_profiles_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        profiles = self.app._profiles_db.get("profiles", {})
        active_id = self.app._active_profile_id

        if not profiles:
            ctk.CTkLabel(self.list_frame, text="No profiles found. Create one below.",
                         text_color=TEXT_MUTED).pack(pady=30)
            return

        for pid, prof in list(profiles.items()):
            is_active = (pid == active_id)
            name = prof.get("name", "User")
            xp = prof.get("xp", 0)
            lvl = self.app._level_for_xp(xp)
            rank = "Rookie"
            for min_lvl, rname in [(1, "Rookie"), (3, "Optic Scout"), (5, "Optic Athlete"), (8, "Vision Master")]:
                if lvl >= min_lvl:
                    rank = rname

            parts = name.split()
            initials = (parts[0][0] + parts[1][0]).upper() if len(parts) >= 2 else (name[:2].upper() or "?")

            card = ctk.CTkFrame(self.list_frame, fg_color=BG_CARD, corner_radius=12,
                                border_width=1, border_color=ACCENT_CYAN if is_active else BORDER_SUBTLE)
            card.pack(fill="x", pady=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=12)

            avatar = ctk.CTkLabel(inner, text=initials, font=ctk.CTkFont(size=12, weight="bold"),
                                  fg_color=ACCENT_GREEN if is_active else ACCENT_PURPLE,
                                  text_color=TEXT_PRIMARY, width=38, height=38, corner_radius=19)
            avatar.pack(side="left", padx=(0, 12))

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            
            top_line = ctk.CTkFrame(info, fg_color="transparent")
            top_line.pack(anchor="w")
            ctk.CTkLabel(top_line, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TEXT_PRIMARY).pack(side="left")
            if is_active:
                ctk.CTkLabel(top_line, text=" (Active User)", font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=ACCENT_GREEN).pack(side="left", padx=4)

            stats_str = f"Level {lvl} · {rank} · {xp} XP"
            ctk.CTkLabel(info, text=stats_str, font=ctk.CTkFont(size=10),
                         text_color=ACCENT_CYAN, anchor="w").pack(anchor="w", pady=(1, 0))

            right_box = ctk.CTkFrame(inner, fg_color="transparent")
            right_box.pack(side="right")

            if is_active:
                lbl = ctk.CTkLabel(right_box, text="✓ ACTIVE", font=ctk.CTkFont(size=10, weight="bold"),
                                   text_color=ACCENT_GREEN, fg_color=BG_CARD_INNER,
                                   corner_radius=6, width=80, height=28)
                lbl.pack(side="left", padx=4)
            else:
                sw_btn = ctk.CTkButton(right_box, text="Switch User", width=88, height=28, corner_radius=8,
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       fg_color=ACCENT_CYAN, text_color=BG_MAIN, hover_color=ACCENT_BLUE,
                                       command=lambda p=pid: self._on_switch(p))
                sw_btn.pack(side="left", padx=4)

            if len(profiles) > 1 and not is_active:
                del_btn = ctk.CTkButton(right_box, text="✕", width=28, height=28, corner_radius=8,
                                        font=ctk.CTkFont(size=11), fg_color=BG_CARD_INNER,
                                        text_color=ACCENT_RED, hover_color="#450a0a",
                                        command=lambda p=pid: self._on_delete(p))
                del_btn.pack(side="left", padx=(2, 0))

    def _on_switch(self, pid):
        self.app.switch_profile(pid)
        self._render_profiles_list()

    def _on_add_new(self):
        val = ctk.CTkInputDialog(text="Enter new user display name:", title="Create Profile").get_input()
        if val and val.strip():
            self.app.create_new_profile(val.strip())
            self._render_profiles_list()

    def _on_guest(self):
        self.app.start_guest_mode()
        self._render_profiles_list()

    def _on_delete(self, pid):
        self.app.delete_profile(pid)
        self._render_profiles_list()

# ══════════════════════════════════════════════════════════════════════════════
#  Always-on-Top Floating Face Cam (Presentation & Screen Recording Mode)
# ══════════════════════════════════════════════════════════════════════════════
class FloatingFaceCamOverlay(ctk.CTkToplevel):
    """
    A compact, borderless/draggable always-on-top webcam overlay window.
    Designed for PPT presentations, remote demos, and video screen recordings:
    keeps the user's face, gaze reticle, and head tracking visible even when
    the main Vision360 window is minimized or behind external apps (e.g. PowerPoint,
    Chrome, Word, Desktop).
    """
    def __init__(self, master, on_close_callback=None):
        super().__init__(master)
        self.on_close_callback = on_close_callback
        self.title("Vision360 // Live Cam")
        self.configure(fg_color=BG_CARD)
        self.attributes('-topmost', True)
        self._last_update_t = 0.0
        self._ctk_img = None
        
        # Window dimensions
        self.cam_size = 200
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        # Default position: bottom-right corner above Windows taskbar
        pos_x = max(10, sw - self.cam_size - 28)
        pos_y = max(10, sh - self.cam_size - 90)
        self.geometry(f"{self.cam_size}x{self.cam_size + 30}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        
        # Mini titlebar for dragging & closing
        self.header = ctk.CTkFrame(self, fg_color=BG_CARD_INNER, height=28, corner_radius=0)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        self.title_lbl = ctk.CTkLabel(
            self.header, text="📹 Vision360 Cam",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=ACCENT_CYAN
        )
        self.title_lbl.pack(side="left", padx=(8, 4), pady=4)
        
        self.close_btn = ctk.CTkButton(
            self.header, text="✕", width=22, height=20, corner_radius=6,
            fg_color="transparent", hover_color="#EF4444", text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self.close
        )
        self.close_btn.pack(side="right", padx=(0, 4), pady=4)
        
        # Video feed frame
        self.video_box = ctk.CTkFrame(self, fg_color=BG_VOID, corner_radius=8,
                                      border_width=1, border_color=BORDER_CARD)
        self.video_box.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.video_lbl = ctk.CTkLabel(self.video_box, text="Live Camera...",
                                      text_color=TEXT_MUTED, font=ctk.CTkFont(size=10))
        self.video_lbl.place(relx=0.5, rely=0.5, anchor="center")
        
        # Dragging handlers
        self._drag_data = {"x": 0, "y": 0}
        self.header.bind("<ButtonPress-1>", self._start_drag)
        self.header.bind("<B1-Motion>", self._do_drag)
        self.title_lbl.bind("<ButtonPress-1>", self._start_drag)
        self.title_lbl.bind("<B1-Motion>", self._do_drag)
        self.video_lbl.bind("<ButtonPress-1>", self._start_drag)
        self.video_lbl.bind("<B1-Motion>", self._do_drag)
        
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._is_active = True

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _do_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    def update_frame(self, cv2_rgb_frame):
        if not self._is_active or not self.winfo_exists():
            return
        now = time.monotonic()
        # Item 6: Cap updates to ~15 fps
        if now - self._last_update_t < (1.0 / 15.0):
            return
        self._last_update_t = now
        try:
            h, w, _ = cv2_rgb_frame.shape
            # Center-crop to square for compact presentation view
            min_dim = min(h, w)
            crop_y = (h - min_dim) // 2
            crop_x = (w - min_dim) // 2
            cropped = cv2_rgb_frame[crop_y:crop_y + min_dim, crop_x:crop_x + min_dim]
            disp_size = self.cam_size - 10
            resized = cv2.resize(cropped, (disp_size, disp_size), interpolation=cv2.INTER_AREA)
            pil_img = Image.fromarray(resized)
            # Item 6: Live frame rendering
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(disp_size, disp_size))
            self._ctk_img = ctk_img
            self.video_lbl.configure(image=ctk_img, text="")
        except Exception:
            pass

    def close(self):
        self._is_active = False
        if self.on_close_callback:
            try:
                self.on_close_callback()
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════════════════════
#  Vision360 Feature Handbook & User Guide Dialog (Help Modal)
# ══════════════════════════════════════════════════════════════════════════════
class FeatureGuideModal(ctk.CTkToplevel):
    """
    Comprehensive in-app handbook explaining every feature, algorithm,
    and biometric pipeline across all Vision360 pages.
    """
    SECTIONS = {
        "◈ Cockpit": {
            "title": "COCKPIT // HEAD TRACKING & BIOMETRICS",
            "desc": "Primary hands-free navigation workspace featuring live camera preview, head tracking, and real-time biometric telemetry.",
            "features": [
                ("🎯 Head Tracking Engine & Reticle", "CORE ENGINE", ACCENT_CYAN,
                 "Maps user head orientation and nose-tip position to on-screen cursor movements with velocity-adaptive smoothing. Operates using standard webcam feeds without specialized hardware.",
                 "Pro Tip: Align camera at eye level approximately 50-65 cm away for stable cursor guidance."),
                ("⚡ Actuation Engine & Click-Mode Dock", "CONTROL DOCK", ACCENT_GREEN,
                 "Executes dwell-based desktop actions (Left, Right, Double, Drag, Scroll, Type) and provides an Always-on-Top floating dock accessible across external applications.",
                 "Pro Tip: Dwell on dock icons to switch click modes on the fly while working in presentations or browsers."),
                ("💡 Ambient Light Guardian", "SCENE SENSOR", ACCENT_AMBER,
                 "Measures webcam scene brightness percentage in real time. Warns when lighting is too dim or produces harsh glare that could impact optical tracking consistency.",
                 "Pro Tip: Maintain balanced ambient illumination to minimize eye strain and optimize camera contrast."),
                ("🔒 Face Mesh Lock & Engine Speed", "TELEMETRY", ACCENT_PURPLE,
                 "Monitors face lock duration (Locked · mm:ss), real webcam frames per second (FPS), and end-to-end computer vision processing latency.",
                 "Pro Tip: If face lock drops, recenter your head within the live camera frame."),
                ("🛑 Mouth Brake & User Distance", "SAFETY & POSTURE", ACCENT_RED,
                 "Provides an emergency pause gesture (opening mouth holds mouse control) and monitors user distance (cm) to detect forward slouching.",
                 "Pro Tip: Open mouth briefly to pause tracking when needing to look away from your screen."),
            ]
        },
        "⚙ Motor": {
            "title": "MOTOR // MOTION DYNAMICS & DWELL CALIBRATION",
            "desc": "Fine-tune cursor projection sensitivity, tremor dampening, dwell trigger thresholds, and edge-scroll boundary zones.",
            "features": [
                ("⏱ Dwell Hold Actuation Engine", "CLICK MECHANISM", ACCENT_CYAN,
                 "Executes clicks when your cursor stays within the jitter deadzone radius for the configured dwell trigger time (adjustable from 0.4s to 2.0s).",
                 "Pro Tip: A circular progress indicator visually counts down dwell hold duration prior to actuation."),
                ("🎯 Tremor Dampening & Practice Sandbox", "STABILIZATION", ACCENT_GREEN,
                 "Applies dynamic smoothing to dampen physiological head tremor. Practice dwell timing in the interactive Dwell Sandbox without affecting external apps.",
                 "Pro Tip: Practice hovering inside the Dwell Sandbox to test your preferred dwell radius and time."),
                ("📜 Smart Zone Scroll & Radar", "SCROLL CONTROL", ACCENT_PURPLE,
                 "Initiates smooth vertical page scrolling when your head tilts into upper or lower trigger zones, with a neutral zone in between to prevent unintended scrolls.",
                 "Pro Tip: Adjust Scroll Speed and Deadzone in Motor settings to match your preferred reading pace."),
                ("🎛 Cursor Projection & Actuation Mechanism", "DIAGNOSTICS", ACCENT_AMBER,
                 "Live coordinate readout displaying projected cursor X/Y coordinates, measured steadiness jitter (in pixels), and active actuation mechanisms.",
                 "Pro Tip: Higher smoothing values yield steadier movement for reading; lower values offer faster response for navigation."),
            ]
        },
        "🫀 EyeRest": {
            "title": "EYEREST // DIGITAL WELLNESS & ERGONOMIC POSTURE",
            "desc": "Biometric wellness suite designed to prevent computer eye strain and anterior head posture during long screen sessions.",
            "features": [
                ("⏳ 20-20-20 Rule Optical Break Engine", "REST CYCLES", ACCENT_CYAN,
                 "Automated timer guiding the 20-20-20 ergonomic guideline: every 20 minutes, look at an object 20 feet away for 20 seconds to relax ocular focus.",
                 "Pro Tip: Complete away-gaze cycles to fill your Daily Wellness Rings and refresh your focus."),
                ("👁 Blink Frequency Biometrics", "BLINK MONITOR", ACCENT_GREEN,
                 "Tracks real-time blinks per minute (BPM) over a 60-second sliding window after 30 seconds of face detection, with a 3-second eyes-open calibration button.",
                 "Pro Tip: Click 'Calibrate Blinks (3s)' while looking naturally at the screen to personalize your blink threshold."),
                ("🧍 3D Posture Guardian", "SPINE ERGONOMICS", ACCENT_PURPLE,
                 "Monitors distance (cm) and lateral head tilt, displaying a responsive wireframe spine that straightens when upright (50+ cm) and flags forward turtle-neck slouching.",
                 "Pro Tip: Keep the wireframe spine in the bio-green upright alignment to avoid cervical neck tension."),
                ("📊 Daily Wellness Rings & Session Analytics", "ANALYTICS", ACCENT_AMBER,
                 "Three concentric activity rings tracking Blinks (Tracking), Breaks (Completed), and Posture (Uptime), alongside composite Fatigue Relief Index.",
                 "Pro Tip: Aim to maintain optimal posture uptime and complete scheduled break cycles throughout your workday."),
            ]
        },
        "♾ EyeGym": {
            "title": "EYEGYM // OCULAR GYMNASTICS & PROGRESSION HUB",
            "desc": "Gamified eye mobility exercises featuring smooth-pursuit tracking, cadence pacing, and XP milestone unlocks.",
            "features": [
                ("♾ Figure-8 Lemniscate & Smooth Pursuit", "MOBILITY EXERCISE", ACCENT_CYAN,
                 "Guides ocular movement along a comfortable infinity curve or horizontal sweep to exercise extraocular muscles and relieve fixed-stare strain.",
                 "Pro Tip: Follow the moving orb smoothly with your reticle; laps increment only when locked on target."),
                ("🎯 Gaze Synchronization Tracking", "SYNC ACCURACY", ACCENT_GREEN,
                 "Measures tracking accuracy between user reticle and guide target in real time. The target glides in sync with active engagement and pauses when idle.",
                 "Pro Tip: Maintain steady lock-on to build your accuracy streak and maximize lap XP rewards."),
                ("⚡ Cadence Pacing & Ocular Perks", "WORKOUT PACING", ACCENT_PURPLE,
                 "Select from Relaxed (14s/lap), Normal (11s/lap), and Agile (8s/lap) speeds. Higher levels unlock enhanced reticle skins and cadence options.",
                 "Pro Tip: Warm up on Relaxed pacing before attempting higher-speed agility cadences."),
                ("🏆 Guided 2-Min Routine & Progression Hub", "XP REWARDS", ACCENT_GOLD,
                 "Complete full circuits to earn XP and level up from Rookie to Master. Start the Guided 2-Minute Eye Routine requiring verified active tracking to earn the +100 XP award.",
                 "Pro Tip: The +100 XP bonus requires continuous focused tracking throughout the 2-minute workout."),
            ]
        },
        "👤 Profile": {
            "title": "PROFILE // WORKSTATION PROFILES & PRESENTATION",
            "desc": "Multi-user workstation settings, ergonomic presets, floating presentation camera, and historical lifetime telemetry.",
            "features": [
                ("👥 Multi-User Workstation Profiles", "PROFILE MANAGER", ACCENT_CYAN,
                 "Create and switch between distinct user profiles on shared computers. Each user retains individual calibration, XP progression, and daily stats.",
                 "Pro Tip: Use the profile switcher dialog to seamlessly change accounts without restarting the application."),
                ("⚡ One-Click Ergonomic Presets", "PRESET CONFIGS", ACCENT_GREEN,
                 "Instantly activate pre-tuned motor configurations: 'Deep Focus & Coding' (steady cursor), 'Casual Browsing & Web' (snappy cursor), or 'Precision Motor Assist' (tremor dampening).",
                 "Pro Tip: Switch presets according to your current task or customize sliders in Motor to create a custom profile."),
                ("📹 Floating Face Cam (Always-on-Top)", "SCREEN RECORDING", ACCENT_PURPLE,
                 "Compact, draggable webcam overlay that stays visible above external presentations (PowerPoint, Zoom, Chrome) to demonstrate hands-free control during screen recordings.",
                 "Pro Tip: Toggle the switch in Profile settings before starting screen recordings for presentations or demonstrations."),
                ("📊 Lifetime Ergonomic Telemetry", "HISTORICAL DATA", ACCENT_AMBER,
                 "Tracks total cumulative hands-free hours, lifetime dwell clicks, overall posture adherence %, and total blinks monitored across all sessions.",
                 "Pro Tip: Lifetime statistics automatically persist across sessions in your local profile store."),
            ]
        }
    }

    def __init__(self, master):
        super().__init__(master)
        self.title("Vision360 // Feature Handbook & User Guide")
        self.geometry("780x600")
        self.minsize(700, 520)
        self.configure(fg_color=BG_VOID)
        self.attributes('-topmost', True)
        
        try:
            self.update_idletasks()
            mx = master.winfo_rootx() + (master.winfo_width() - 780) // 2
            my = master.winfo_rooty() + (master.winfo_height() - 600) // 2
            self.geometry(f"+{max(20, mx)}+{max(20, my)}")
        except Exception:
            pass
        
        self.bind("<Escape>", lambda e: self.destroy())
        self._current_cat = "◈ Cockpit"
        self._build_ui()

    def _build_ui(self):
        # Header bar
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        header.pack(fill="x", padx=0, pady=(0, 10))
        
        top_h = ctk.CTkFrame(header, fg_color="transparent")
        top_h.pack(fill="x", padx=20, pady=14)
        
        title_box = ctk.CTkFrame(top_h, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)
        
        t_row = ctk.CTkFrame(title_box, fg_color="transparent")
        t_row.pack(anchor="w")
        
        ctk.CTkLabel(t_row, text="📖", font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(t_row, text="VISION360 // SYSTEM HANDBOOK & FEATURE GUIDE",
                     font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        
        ctk.CTkLabel(title_box, text="Comprehensive operational manual for hands-free computing, ocular ergonomics & telemetry",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", pady=(3, 0))
        
        close_btn = ctk.CTkButton(top_h, text="✕", width=28, height=28, corner_radius=14,
                                  fg_color=BG_CARD_INNER, hover_color=BORDER_CARD,
                                  text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold"),
                                  command=self.destroy)
        close_btn.pack(side="right")
        
        # Category Selector Tabs
        cat_bar = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_CARD)
        cat_bar.pack(fill="x", padx=20, pady=(0, 12))
        
        self.cat_btns = {}
        cats = ["◈ Cockpit", "⚙ Motor", "🫀 EyeRest", "♾ EyeGym", "👤 Profile"]
        for cat in cats:
            btn = ctk.CTkButton(
                cat_bar, text=cat, font=ctk.CTkFont(size=12, weight="bold"),
                height=34, corner_radius=8,
                fg_color="transparent", text_color=TEXT_SECONDARY,
                hover_color=BG_CARD_INNER,
                command=lambda c=cat: self._select_category(c)
            )
            btn.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            self.cat_btns[cat] = btn
            
        # Section Title & Subtitle Container
        self.info_header = ctk.CTkFrame(self, fg_color="transparent")
        self.info_header.pack(fill="x", padx=24, pady=(0, 8))
        
        self.lbl_sec_title = ctk.CTkLabel(self.info_header, text="", font=ctk.CTkFont(size=13, weight="bold"),
                                          text_color=ACCENT_CYAN, anchor="w")
        self.lbl_sec_title.pack(anchor="w")
        self.lbl_sec_desc = ctk.CTkLabel(self.info_header, text="", font=ctk.CTkFont(size=11),
                                         text_color=TEXT_SECONDARY, anchor="w")
        self.lbl_sec_desc.pack(anchor="w", pady=(2, 0))
        
        # Scrollable Cards Container
        self.content_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        
        self._select_category("◈ Cockpit")

    def _select_category(self, cat):
        self._current_cat = cat
        for c, btn in self.cat_btns.items():
            if c == cat:
                btn.configure(fg_color=BG_ELEVATED, text_color=ACCENT_CYAN)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
                
        sec_data = self.SECTIONS.get(cat, {})
        self.lbl_sec_title.configure(text=sec_data.get("title", ""))
        self.lbl_sec_desc.configure(text=sec_data.get("desc", ""))
        
        # Clear existing cards
        for w in self.content_scroll.winfo_children():
            w.destroy()
            
        # Render feature cards
        for title, tag, tag_color, desc, tip in sec_data.get("features", []):
            card = ctk.CTkFrame(self.content_scroll, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=BORDER_CARD)
            card.pack(fill="x", pady=(0, 12))
            
            # Header row inside card: Title + Tag pill
            head = ctk.CTkFrame(card, fg_color="transparent")
            head.pack(fill="x", padx=16, pady=(14, 6))
            
            ctk.CTkLabel(head, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TEXT_PRIMARY, anchor="w").pack(side="left")
            
            tag_pill = ctk.CTkLabel(head, text=tag, font=ctk.CTkFont(size=10, weight="bold"),
                                    fg_color=BG_CARD_INNER, text_color=tag_color,
                                    corner_radius=8, padx=8, pady=2)
            tag_pill.pack(side="right")
            
            # Feature description (Item 9: Dynamic wraplength)
            desc_lbl = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY,
                                    anchor="w", justify="left", wraplength=680)
            desc_lbl.pack(anchor="w", padx=16, pady=(0, 8))
            
            # Pro tip box
            tip_box = ctk.CTkFrame(card, fg_color=BG_CARD_INNER, corner_radius=8)
            tip_box.pack(fill="x", padx=14, pady=(0, 12))
            
            tip_lbl = ctk.CTkLabel(tip_box, text=f"💡 {tip}", font=ctk.CTkFont(size=10),
                                   text_color=TEXT_MUTED, anchor="w", justify="left", wraplength=670)
            tip_lbl.pack(anchor="w", padx=10, pady=6)
            
            def _on_card_cfg(event, dl=desc_lbl, tl=tip_lbl):
                w = max(240, event.width - 36)
                dl.configure(wraplength=w)
                tl.configure(wraplength=max(200, w - 24))
            card.bind("<Configure>", _on_card_cfg)

# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-FIDELITY CANVASES: Cyberpunk Dashboard Gauges
# ══════════════════════════════════════════════════════════════════════════════
GLOW_MAP = {
    ACCENT_GREEN: "#065F46",
    ACCENT_AMBER: "#92400E",
    ACCENT_RED:   "#9F1239",
    ACCENT_CYAN:  "#0C4A6E",
}

class CyberpunkGaugeCanvas(ctk.CTkCanvas):
    """
    Cyberpunk Dashboard Gauge Canvas:
      - Thick segmented outer ring (small dashed arcs with active dynamic coloring)
      - Inner glowing solid arc representing current value
      - Solid dark background circle core behind value with glowing neon rim
      - Dynamic Color Logic: Green / Amber / Red based on health thresholds
      - Clean typography: large central readout and centered subtitle
    """
    def __init__(self, master, width=220, height=200, gauge_type="bpm", title="", **kwargs):
        super().__init__(master, width=width, height=height, bg=BG_CARD_INNER, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.gauge_type = gauge_type.lower()
        self.title = title if title else ("Blink Frequency" if self.gauge_type == "bpm" else "20-20-20 Rule")

        # State variables (BPM starts as None = "still measuring", never a fake number)
        self.value = None if self.gauge_type == "bpm" else 0.0
        self.min_val = 0.0
        self.max_val = 35.0
        self.remaining_sec = 1200.0
        self.total_sec = 1200.0
        self.status = "Measuring" if self.gauge_type == "bpm" else "On Track"
        self.active_color = TEXT_MUTED if self.gauge_type == "bpm" else ACCENT_GREEN
        self._last_snapshot = None

        self.bind("<Configure>", self._on_configure)
        self._update_state()
        self._draw()

    def _on_configure(self, event):
        if event.width > 50 and event.height > 50:
            if event.width != self.w or event.height != self.h:
                self.w, self.h = event.width, event.height
                self._draw()

    def set_value(self, bpm, status: str = None):
        """Used for BPM mode. Pass None while the rate is still being measured."""
        self.value = None if bpm is None else max(self.min_val, min(self.max_val, float(bpm)))
        self._update_state()
        if status:
            self.status = status
        snap = (None if self.value is None else round(self.value, 1), self.active_color, self.status)
        if snap == self._last_snapshot:
            return
        self._last_snapshot = snap
        self._draw()

    def set_timer(self, remaining_sec: float, total_sec: float = 1200.0, elapsed_mins: int = None):
        """Used for 20-20-20 Rule countdown mode."""
        remaining_sec = max(0.0, float(remaining_sec))
        total_sec = max(1.0, float(total_sec))
        snap = (int(remaining_sec), int(total_sec))
        if snap == self._last_snapshot:
            return
        self._last_snapshot = snap
        self.remaining_sec = remaining_sec
        self.total_sec = total_sec
        self._update_state()
        self._draw()

    def _update_state(self):
        """Calculates dynamic health threshold colors and status."""
        if self.gauge_type == "bpm":
            if self.value is None:
                self.active_color = TEXT_MUTED
                self.status = "Measuring"
            elif self.value >= 14.0:
                self.active_color = ACCENT_GREEN
                self.status = "Optimal"
            elif 10.0 <= self.value < 14.0:
                self.active_color = ACCENT_AMBER
                self.status = "Average"
            else:
                self.active_color = ACCENT_RED
                self.status = "Fatigued"
        else:
            remaining_mins = self.remaining_sec / 60.0
            if remaining_mins > 10.0:
                self.active_color = ACCENT_GREEN
                self.status = "On Track"
            elif 3.0 <= remaining_mins <= 10.0:
                self.active_color = ACCENT_AMBER
                self.status = "Attention"
            else:
                self.active_color = ACCENT_RED
                self.status = "Break Due"

    def _draw(self):
        self.delete("all")
        pad = 14

        # Title top-left
        self.create_text(pad, 14, text=self.title, fill=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"), anchor="w")

        # Geometry calculations
        cx = self.w / 2.0
        cy = max(60.0, (self.h + 16.0) / 2.0)
        avail_r = min((self.w - 32.0) / 2.0, (self.h - 42.0) / 2.0)
        r_outer = min(82.0, max(50.0, avail_r))
        r_mid = max(38.0, r_outer - 13.0)
        r_core = max(26.0, r_mid - 16.0)

        # Gauge sweep: 220 deg (bottom-left) clockwise by -260 deg (ending at 320 deg)
        start_ang, total_sweep = 220.0, -260.0

        if self.gauge_type == "bpm":
            if self.value is None:
                frac, val_str = 0.0, "--"
            else:
                frac = min(1.0, max(0.0, (self.value - self.min_val) / (self.max_val - self.min_val)))
                val_str = f"{int(round(self.value))}"
            sub_str = "BPM"
        else:
            frac = min(1.0, max(0.0, self.remaining_sec / self.total_sec))
            m, s = divmod(int(self.remaining_sec), 60)
            val_str = f"{m:02d}:{s:02d}"
            sub_str = "Mins left"

        extent = total_sweep * frac
        glow_color = GLOW_MAP.get(self.active_color, "#1E293B")

        # ── 1. Thick Segmented Outer Ring (360 deg dashed arcs) ───────────────
        dash_step = 6.0
        dash_len = 3.6
        for deg in range(0, 360, int(dash_step)):
            cw_offset = (start_ang - deg) % 360.0
            if cw_offset <= abs(extent) and abs(extent) > 0.5:
                seg_col = self.active_color
            elif cw_offset <= abs(total_sweep):
                seg_col = "#15243F"
            else:
                seg_col = "#0D172A"

            self.create_arc(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer,
                            start=deg, extent=dash_len, style="arc", outline=seg_col, width=3.5)

        # ── 2. Inner Glowing Solid Arc (Track & Active Value) ──────────────────
        # Dark background track
        self.create_arc(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid,
                        start=start_ang, extent=total_sweep, style="arc", outline="#131E33", width=9)
        # Subtle guide tracks
        self.create_arc(cx - (r_mid + 5), cy - (r_mid + 5), cx + (r_mid + 5), cy + (r_mid + 5),
                        start=start_ang, extent=total_sweep, style="arc", outline="#1A2944", width=1)
        self.create_arc(cx - (r_mid - 5), cy - (r_mid - 5), cx + (r_mid - 5), cy + (r_mid - 5),
                        start=start_ang, extent=total_sweep, style="arc", outline="#1A2944", width=1)

        # Active glowing arc
        if abs(extent) > 0.5:
            # Outer soft bloom / glow
            self.create_arc(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid,
                            start=start_ang, extent=extent, style="arc", outline=glow_color, width=13)
            # Core solid neon arc
            self.create_arc(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid,
                            start=start_ang, extent=extent, style="arc", outline=self.active_color, width=8)

            # Glowing tip needle marker
            tip_rad = math.radians(start_ang + extent)
            kx = cx + r_mid * math.cos(tip_rad)
            ky = cy - r_mid * math.sin(tip_rad)
            self.create_oval(kx - 4, ky - 4, kx + 4, ky + 4, fill="#FFFFFF", outline=self.active_color, width=1.5)

        # ── 3. Solid Background Circle Core Behind Value ───────────────────────
        # Soft outer glow ring
        self.create_oval(cx - (r_core + 2), cy - (r_core + 2), cx + (r_core + 2), cy + (r_core + 2),
                         outline=glow_color, width=3)
        # Main solid dark disc with neon rim
        self.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core,
                         fill="#090E1B", outline=self.active_color, width=2)

        # ── 4. Clean Typography ───────────────────────────────────────────────
        val_font_size = max(14, int(r_core * 0.44))
        sub_font_size = max(8, int(r_core * 0.20))

        # Central value (changes dynamically to active_color)
        self.create_text(cx, cy - int(r_core * 0.16), text=val_str, fill=self.active_color,
                         font=("Consolas", val_font_size, "bold"))
        # Subtitle
        self.create_text(cx, cy + int(r_core * 0.32), text=sub_str, fill=TEXT_SECONDARY,
                         font=("Segoe UI", sub_font_size, "bold"))

        # Bottom status readout (Cyberpunk HUD style)
        self.create_text(cx, cy + r_core + 12, text=f"// {self.status.upper()} //",
                         fill=self.active_color, font=("Consolas", 8, "bold"))

# Backwards compatibility aliases
BlinkFrequencyCanvas = CyberpunkGaugeCanvas
Rule2020Canvas = CyberpunkGaugeCanvas


class CircularGaugeCanvas(ctk.CTkCanvas):
    """High-contrast tachometer gauge for Blink Rate (BPM)."""
    def __init__(self, master, size=150, title="BPM", min_val=0, max_val=35, **kwargs):
        super().__init__(master, width=size, height=size, bg=BG_CARD, highlightthickness=0, **kwargs)
        self.size = size
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.value = 18.0
        self.color = ACCENT_GREEN
        self.subtitle = "Healthy"
        self._draw()

    def set_value(self, val: float, color: str = None, subtitle: str = None):
        self.value = max(self.min_val, min(self.max_val, val))
        if color: self.color = color
        if subtitle: self.subtitle = subtitle
        self._draw()

    def _draw(self):
        self.delete("all")
        pad = 16
        cx, cy = self.size / 2, self.size / 2
        
        self.create_oval(pad - 4, pad - 4, self.size - pad + 4, self.size - pad + 4, outline=BG_ELEVATED, width=1)
        self.create_arc(pad, pad, self.size - pad, self.size - pad,
                        start=135, extent=-270, style="arc", outline=BORDER_SUBTLE, width=10)
        
        fraction = (self.value - self.min_val) / max(1, (self.max_val - self.min_val))
        extent_angle = -270 * fraction
        
        self.create_arc(pad, pad, self.size - pad, self.size - pad,
                        start=135, extent=extent_angle, style="arc", outline=self.color, width=10)
        
        val_str = f"{int(self.value)}"
        self.create_text(cx, cy - 8, text=val_str, fill=TEXT_PRIMARY, font=("Consolas", 26, "bold"))
        self.create_text(cx, cy + 18, text=self.title, fill=TEXT_MUTED, font=("Segoe UI", 10, "bold"))
        if self.subtitle:
            self.create_text(cx, cy + 32, text=self.subtitle, fill=self.color, font=("Segoe UI", 10, "bold"))


# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-FIDELITY CANVAS 1: Live 3D Posture Guardian (Dynamic Biomechanical Spine)
# ══════════════════════════════════════════════════════════════════════════════
class PostureSpineCanvas(ctk.CTkCanvas):
    """
    Renders an interactive, biomechanically-animated 3D wireframe human body
    and spine that dynamically bends and curves according to the user's posture:
      - Sitting upright / correct posture (dist ~ 56-65 cm):
        Spine straightens to normal vertical ergonomic alignment with radiant Bio-Green (#10B981) glow.
      - Leaning forward toward the monitor (dist < 52 cm down to 30 cm):
        Spine visibly arches forward into a hunched curve, shifting to Cautionary Amber (#F59E0B)
        and Critical Alert Red (#EF4444) when severe turtle-neck is detected.
      - Tilting / lateral bending:
        Spine flexes laterally to mirror head roll and posture tilt in real time.
    """
    def __init__(self, master, width=280, height=360, **kwargs):
        super().__init__(master, width=width, height=height, bg=BG_CARD, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.distance_cm = 60.0
        self.tilt_deg = 0.0
        self.is_slouching = False
        self.has_data = False      # False until a real distance reading arrives
        
        # Target metrics
        self._target_lean = 0.0   # 0.0 = erect/upright, 1.0 = severely hunched
        self._target_tilt = 0.0   # -1.0 to 1.0 = lateral tilt
        
        # Smoothed values for fluid organic animation
        self._smooth_lean = 0.0
        self._smooth_tilt = 0.0
        self._last_rendered_lean = -999.0
        self._last_rendered_tilt = -999.0
        
        # Raw base asset & coordinate grids
        self._raw_bgr = None
        self._mask_green = None
        self._y_coords = None
        self._x_coords = None
        self._env_x = None
        self._bg_photo = None
        
        self._load_wireframe_asset()
        self.bind("<Configure>", self._on_configure)
        self._draw_initial()
        self._animate_tick()

    def _on_configure(self, event):
        """Dynamically fit and center the wireframe body to the canvas container."""
        if event.width > 60 and event.height > 60:
            if event.width != self.w or event.height != self.h:
                self.w = event.width
                self.h = event.height
                self._render_warped_spine()

    def _load_wireframe_asset(self):
        asset_path = resource_path("assets", "posture_wireframe.png")
        if asset_path.exists():
            try:
                bgr = cv2.imread(str(asset_path))
                if bgr is not None:
                    self._raw_bgr = bgr
                    h, w = bgr.shape[:2]
                    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
                    mask_raw = cv2.inRange(hsv, (35, 45, 35), (85, 255, 255)).astype(np.float32) / 255.0
                    # Gaussian blur to soften the spine mask for realistic organic glow without blocky edges
                    self._mask_green = cv2.GaussianBlur(mask_raw, (5, 5), 1.2)
                    self._y_coords, self._x_coords = np.mgrid[0:h, 0:w].astype(np.float32)
                    center_x = w / 2.0
                    # Gaussian envelope focused on torso and spine
                    self._env_x = np.exp(-((self._x_coords - center_x) / 52.0) ** 2)
            except Exception:
                self._raw_bgr = None

    def set_posture(self, dist_cm, tilt_deg: float = 0.0):
        """Update live posture metrics from vision pipeline (None = no face)."""
        if dist_cm is None:
            if self.has_data:
                self.has_data = False
                self.is_slouching = False
                self._target_lean = 0.0
                self._target_tilt = 0.0
                self._last_rendered_lean = -999.0   # force a redraw
            return
        if not self.has_data:
            self.has_data = True
            self._last_rendered_lean = -999.0       # force a redraw
        self.distance_cm = dist_cm
        self.tilt_deg = tilt_deg
        self.is_slouching = dist_cm < 46.0
        
        # Map distance to forward hunch factor:
        # At >= 58 cm: 0.0 (upright)
        # At 50 cm: ~0.35 (leaning in)
        # At <= 36 cm: 1.0 (severe turtle neck)
        if dist_cm >= 58.0:
            self._target_lean = 0.0
        elif dist_cm >= 48.0:
            self._target_lean = (58.0 - dist_cm) / 10.0 * 0.40
        else:
            self._target_lean = 0.40 + (48.0 - dist_cm) / 16.0 * 0.60
        self._target_lean = float(np.clip(self._target_lean, 0.0, 1.0))
        
        # Map lateral tilt:
        self._target_tilt = float(np.clip(tilt_deg / 22.0, -1.0, 1.0))

    def _animate_tick(self):
        """High-performance spring physics for organic, non-jittery spine movement."""
        # Item 5: Skip drawing unless viewable
        if not self.winfo_viewable():
            self.after(100, self._animate_tick)
            return

        # Spring interpolation
        self._smooth_lean += (self._target_lean - self._smooth_lean) * 0.22
        self._smooth_tilt += (self._target_tilt - self._smooth_tilt) * 0.22
        
        # Re-render if changed meaningfully or if initial
        if (abs(self._smooth_lean - self._last_rendered_lean) > 0.008 or
            abs(self._smooth_tilt - self._last_rendered_tilt) > 0.008):
            self._last_rendered_lean = self._smooth_lean
            self._last_rendered_tilt = self._smooth_tilt
            self._render_warped_spine()

        self.after(33, self._animate_tick)  # ~30 FPS fluid animation

    def _render_warped_spine(self):
        if self._raw_bgr is None:
            self._draw_fallback()
            return
            
        h, w = self._raw_bgr.shape[:2]
        lean = self._smooth_lean
        tilt = self._smooth_tilt
        
        # Vertical normalized height: 0 at base (pelvis), 1 at top (cervical/head)
        t_vert = (h - self._y_coords) / float(h)
        
        # Forward lean bends cervical/thoracic spine forward & arched
        dx_forward = 34.0 * lean * (np.sin(np.pi * 0.75 * t_vert) ** 1.3) * self._env_x
        dy_forward = 9.0 * lean * (t_vert ** 1.8) * self._env_x
        
        # Lateral tilt bends spine sideways
        dx_lateral = 22.0 * tilt * (t_vert ** 1.5) * self._env_x
        
        cur_map_x = self._x_coords - (dx_forward + dx_lateral)
        cur_map_y = self._y_coords + dy_forward
        
        warped = cv2.remap(self._raw_bgr, cur_map_x, cur_map_y, cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=(11, 21, 40))
        
        # Dynamic spine glow color transition:
        # Green (#10B981) -> Amber (#F59E0B) -> Crimson Red (#EF4444)
        if lean > 0.08:
            warped_mask = cv2.remap(self._mask_green, cur_map_x, cur_map_y, cv2.INTER_LINEAR)
            w_mask_3d = np.repeat(warped_mask[:, :, np.newaxis], 3, axis=2)
            if lean < 0.45:
                tc = lean / 0.45
                target_bgr = np.array([40*(1-tc) + 15*tc, 220*(1-tc) + 155*tc, 90*(1-tc) + 245*tc], dtype=np.float32)
            else:
                tc = min(1.0, (lean - 0.45) / 0.55)
                target_bgr = np.array([15*(1-tc) + 30*tc, 155*(1-tc) + 40*tc, 245*(1-tc) + 240*tc], dtype=np.float32)
                
            warped = np.clip(warped.astype(np.float32) * (1.0 - w_mask_3d * 0.75) + target_bgr * (w_mask_3d * 0.85), 0, 255).astype(np.uint8)

        # Convert warped BGR image to PhotoImage
        rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        
        # Scale proportionally to fill the card box
        avail_w = max(50, self.w - 16)
        avail_h = max(50, self.h - 60)  # Leave room for bottom status label
        scale = min(avail_w / pil_img.width, avail_h / pil_img.height)
        target_w = max(10, int(pil_img.width * scale))
        target_h = max(10, int(pil_img.height * scale))
        
        scaled_img = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        self._bg_photo = ImageTk.PhotoImage(scaled_img)
        
        self._update_canvas(avail_h)

    def _update_canvas(self, avail_h=None):
        self.delete("all")
        cx = self.w / 2
        
        if avail_h is None:
            avail_h = max(50, self.h - 60)
        cy = (avail_h / 2) + 4

        # Center the image in the canvas box
        if self._bg_photo:
            self.create_image(cx, cy, image=self._bg_photo, anchor="center")

        # Dynamic Status Text Overlay
        if not self.has_data:
            glow_color = TEXT_MUTED
            status_text = "Waiting for face…"
        elif self._smooth_lean >= 0.50 or self.is_slouching:
            glow_color = ACCENT_RED
            status_text = f"⚠️ Turtle Neck at {int(self.distance_cm)} cm\n(Straighten Spine)"
        elif self._smooth_lean >= 0.20 or self.distance_cm < 52.0:
            glow_color = ACCENT_AMBER
            status_text = f"Leaning close at {int(self.distance_cm)} cm"
        else:
            glow_color = ACCENT_GREEN
            status_text = f"Perfect posture at {int(self.distance_cm)} cm"

        # Position with 18px margin from bottom, growing upward
        self.create_text(
            cx, self.h - 18, 
            text=status_text, 
            fill=glow_color,
            font=("Segoe UI", 11, "bold"), 
            justify="center",
            anchor="s"  
        )
    def _draw_fallback(self):
        self.delete("all")
        cx = self.w / 2
        cy = (self.h - 28) / 2
        self.create_oval(cx - 24, cy - 80, cx + 24, cy - 30, outline=ACCENT_CYAN, width=1)
        for i, y_n in enumerate(range(int(cy - 25), int(cy + 95), 15)):
            bend_off = int(self._smooth_lean * 24.0 * math.sin(i / 8.0 * math.pi) + self._smooth_tilt * 16.0)
            col = ACCENT_RED if self._smooth_lean > 0.5 else (ACCENT_AMBER if self._smooth_lean > 0.2 else ACCENT_GREEN)
            self.create_oval(cx + bend_off - 5, y_n - 3, cx + bend_off + 5, y_n + 3, fill=col, outline=TEXT_PRIMARY, width=1)
        
        glow_color = ACCENT_RED if self._smooth_lean > 0.5 else (ACCENT_AMBER if self._smooth_lean > 0.2 else ACCENT_GREEN)
        fb_text = f"Posture at {int(self.distance_cm)} cm" if self.has_data else "Waiting for face…"
        if not self.has_data: glow_color = TEXT_MUTED
        self.create_text(cx, self.h - 14, text=fb_text, fill=glow_color, font=("Segoe UI", 11, "bold"))

    def _draw_initial(self):
        self._render_warped_spine()


# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-FIDELITY CANVAS 2: Gamified Figure-8 Eye Gymnastics (Cyberpunk Glow & Telemetry)
# ══════════════════════════════════════════════════════════════════════════════
class Figure8GymCanvas(ctk.CTkCanvas):
    """
    Renders the Gamified Figure-8 Eye Gymnastics matching Image 2 & 4:
    - Ergonomically optimized lemniscate: compact horizontal width (relieves neck strain)
      and spacious vertical circular lobes for comfortable ocular mobility.
    - Interactive Gaze-Tracing Engine: User moves their head/cursor along the neon track.
      The guide orb advances with the user, rewarding XP proportional to true traced accuracy.
      No free XP or automated ball running when AFK.
    - 3 Concentric nested glowing infinity rails (outer, middle, inner) with multi-layer bloom.
    - Left Lobe: Glowing Neon Cyan with dual-gradient infinity glyph (∞) in center.
    - Right Lobe: Glowing Electric Violet with cyan/gold target crosshair reticle (┼).
    - Luminous traced beam illuminating the exact circuit sector traced by the user.
    - Guide orb with stardust particle spray and exact right-angle leader line callouts.
    - Top & Bottom telemetry pills: [Accuracy %] [Streak xN] [+XP Awarded].
    - Exponential moving average (EMA) smoothing for neck relaxation.
    """
    def __init__(self, master, width=540, height=270, on_lap=None, master_app=None, **kwargs):
        super().__init__(master, width=width, height=height, bg=BG_CARD, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.t = 0.0
        self.is_running = True
        self.speed_mult = 1.0
        self.pattern = "figure8"     # 'figure8' or 'horizontal'
        self.laps_done = 0
        self.accuracy = 95.0
        self.has_tracked = False
        self.locked = False
        self.on_lap = on_lap
        self.master_app = master_app
        self.target_user_x = width / 2
        self.target_user_y = height / 2
        self.user_x = width / 2
        self.user_y = height / 2
        self.particles = collections.deque(maxlen=24)
        self.lap_acc_samples = []
        self.lap_locked_samples = 0
        self.last_awarded_xp = 50
        self.last_lap_acc = 95.0
        self._rails_drawn = False
        self._cached_scale_key = None
        self.bind("<Configure>", self._on_configure)
        self.bind("<Motion>", self._on_mouse_move)
        self._animate()

    def _on_configure(self, event):
        if event.width > 60 and event.height > 60:
            if event.width != self.w or event.height != self.h:
                self.w, self.h = event.width, event.height
                self._rails_drawn = False

    def _on_mouse_move(self, event):
        # Support fluid tracking via mouse cursor or mouse hover practice
        if not getattr(self.master_app, '_face_present', False) or getattr(self.master_app, '_mouse_on', False):
            self.target_user_x = event.x
            self.target_user_y = event.y
            self.has_tracked = True

    def update_gaze_pos(self, norm_x, norm_y):
        cx, cy = self.w / 2, self.h / 2
        # Use calibrated neutral zero-point center
        center_x = getattr(self.master_app, '_neutral_x', 0.5) if self.master_app else 0.5
        center_y = getattr(self.master_app, '_neutral_y', 0.5) if self.master_app else 0.5
        
        # Comfortable, natural neck rotation gain (±0.09 head tilt reaches full orbital range comfortably)
        dx = (norm_x - center_x) * 4.4
        dy = (norm_y - center_y) * 4.0
        self.target_user_x = cx + max(-0.42, min(0.42, dx)) * self.w
        self.target_user_y = cy + max(-0.38, min(0.38, dy)) * self.h
        self.has_tracked = True

    def set_speed(self, speed):
        self.speed_mult = max(0.4, min(2.5, float(speed)))

    def set_pattern(self, pattern_name):
        if pattern_name in ("figure8", "horizontal"):
            self.pattern = pattern_name
            self.t = 0.0
            self.particles.clear()
            self.lap_acc_samples.clear()
            self.lap_locked_samples = 0
            self._rails_drawn = False
            self._draw()

    def toggle_play(self):
        self.is_running = not self.is_running
        return self.is_running

    def reset_laps(self):
        self.laps_done = 0
        self.t = 0.0
        self.particles.clear()
        self.lap_acc_samples.clear()

    def _get_track_point(self, theta, scale=1.0):
        """Calculates track coordinates: compact width horizontally, wide circular lobes vertically."""
        cx, cy = self.w / 2, self.h / 2
        if self.pattern == "figure8":
            # Ergonomic Figure-8: compact horizontal span (0.22w) with plump vertical lobes (0.72h)
            a = self.w * 0.22 * scale
            b = self.h * 0.72 * scale
            denom = 1 + math.sin(theta)**2
            px = cx + (a * math.cos(theta)) / denom
            py = cy + (b * math.sin(theta) * math.cos(theta)) / denom
        else:
            # Smooth Pursuit: Generous horizontal stadium track (0.34w) with gentle vertical sweep (0.28h)
            a = self.w * 0.34 * scale
            b = self.h * 0.28 * scale
            px = cx + (a * math.cos(theta))
            py = cy + (b * math.sin(theta))
        return px, py

    def _animate(self):
        # Item 5: Skip drawing unless winfo_viewable() is true
        if not self.winfo_viewable():
            self.after(100, self._animate)
            return

        is_gym_tab = True
        if self.master_app and hasattr(self.master_app, '_current_tab'):
            is_gym_tab = ('EyeGym' in getattr(self.master_app, '_current_tab', ''))

        face_on = getattr(self.master_app, '_face_present', True) if self.master_app else True

        if self.is_running and is_gym_tab and face_on:
            # Velocity-adaptive exponential filter for fluid neck comfort (zero lag on turn, rock-steady hold):
            pos_delta = math.hypot(self.target_user_x - self.user_x, self.target_user_y - self.user_y)
            adaptive_alpha = 0.20 + min(0.18, (pos_delta / 70.0) * 0.18)
            self.user_x += (self.target_user_x - self.user_x) * adaptive_alpha
            self.user_y += (self.target_user_y - self.user_y) * adaptive_alpha

            # Compute current guide orb position on track
            orb_x, orb_y = self._get_track_point(self.t, scale=1.0)
            dist_to_orb = math.hypot(self.user_x - orb_x, self.user_y - orb_y)

            base_dt = (2.0 * math.pi * 0.028) / 11.0

            # Active Gaze Tracing: The ball ONLY glides when the user is actively following it!
            # If the user is idle, not tracking, or reticle is away, the ball pauses and holds position!
            if self.has_tracked and dist_to_orb <= 65.0:
                # User is locked onto guide orb: smooth forward glide, top accuracy
                self.locked = True
                self.lap_locked_samples += 1
                dt = base_dt * self.speed_mult
                self.t += dt
                inst_acc = max(70.0, min(99.8, 100.0 - (dist_to_orb / 65.0) * 30.0))
                self.lap_acc_samples.append(inst_acc)
                self.accuracy = self.accuracy * 0.90 + inst_acc * 0.10
            elif self.has_tracked and dist_to_orb <= 90.0:
                # User is trailing slightly: orb gently glides in sync so user can stay on track
                self.locked = False
                catchup_ratio = max(0.15, (90.0 - dist_to_orb) / 25.0)
                dt = base_dt * self.speed_mult * catchup_ratio
                self.t += dt
                inst_acc = max(40.0, 75.0 - ((dist_to_orb - 65.0) / 25.0) * 35.0)
                self.lap_acc_samples.append(inst_acc)
                self.accuracy = self.accuracy * 0.94 + inst_acc * 0.06
            else:
                # User stopped, looked away, or not interacting:
                # FREEZE the ball at current spot! NO automatic movement, NO automatic laps or XP!
                self.locked = False
                dt = 0.0
                if self.has_tracked:
                    self.accuracy = max(20.0, self.accuracy * 0.99)

            # Check for completed circuit (full 360° circuit traced by user)
            # Item 12: Count laps ONLY when user was actually locked on target!
            if self.t >= 2 * math.pi:
                self.t -= 2 * math.pi
                samples_collected = len(self.lap_acc_samples)
                locked_count = getattr(self, 'lap_locked_samples', 0)
                avg_acc = (sum(self.lap_acc_samples) / max(1, samples_collected)) if self.lap_acc_samples else 0.0
                self.lap_acc_samples.clear()
                self.lap_locked_samples = 0

                # Must have at least 25 locked samples and average accuracy >= 65% to count as a genuine tracked lap
                if samples_collected >= 35 and locked_count >= 25 and avg_acc >= 65.0:
                    self.laps_done += 1
                    # Award XP scaled by actual traced accuracy
                    earned_xp = int(round(50.0 * (avg_acc / 100.0)))
                    earned_xp = max(15, min(50, earned_xp))
                    self.last_awarded_xp = earned_xp
                    self.last_lap_acc = avg_acc
                    if callable(self.on_lap):
                        try: self.on_lap(self.laps_done, earned_xp, avg_acc)
                        except Exception: pass
                else:
                    if self.master_app and hasattr(self.master_app, '_ts_status'):
                        self.master_app._ts_status("⚠️ Lap incomplete: Reticle must lock onto moving orb to register lap!", color=ACCENT_AMBER)

            self._draw()
        elif is_gym_tab:
            # When paused, keep rendering current state
            self._draw()

        self.after(28, self._animate)

    def _draw_pill(self, x, y, text, fg_col, border_col, bg_col):
        """Draws a sleek rounded cyberpunk telemetry pill with proper padding and width."""
        font = ("Segoe UI", 9, "bold")
        pad_x = 10
        pad_y = 4
        # Calculate width so text never clips or overflows
        char_w = 8.5
        text_w = max(68, int(len(text) * char_w) + (pad_x * 2))
        x0, y0 = x, y - pad_y - 8
        x1, y1 = x + text_w, y + pad_y + 8
        r = (y1 - y0) / 2
        
        self.create_oval(x0, y0, x0 + r*2, y1, fill=bg_col, outline=border_col, width=1, tags=("moving",))
        self.create_oval(x1 - r*2, y0, x1, y1, fill=bg_col, outline=border_col, width=1, tags=("moving",))
        self.create_rectangle(x0 + r, y0, x1 - r, y1, fill=bg_col, outline="", width=0, tags=("moving",))
        self.create_line(x0 + r, y0, x1 - r, y0, fill=border_col, width=1, tags=("moving",))
        self.create_line(x0 + r, y1, x1 - r, y1, fill=border_col, width=1, tags=("moving",))
        self.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=text, fill=fg_col, font=font, tags=("moving",))
        return x1 + 14  # 14px clean spacing between adjacent pills

    def _draw_static_rails(self):
        """Draws the static background rails, center emblems, and fixed annotations once."""
        self.delete("static_rails")
        cx, cy = self.w / 2, self.h / 2
        lvl = getattr(self.master_app, '_player_level', 1) if self.master_app else 1
        emerald_active = (lvl >= 2)
        gold_reticle = (lvl >= 3)

        # Deep ambient card background
        self.create_rectangle(0, 0, self.w, self.h, fill=BG_CARD, outline="", tags=("static_rails",))

        rail_scales = [1.10, 1.00, 0.90]
        steps_half = 48
        left_track_col = "#10B981" if emerald_active else ACCENT_CYAN
        left_glow_col = "#043B2C" if emerald_active else "#042D45"
        right_track_col = ACCENT_PURPLE
        right_glow_col = "#290D45"

        for scale in rail_scales:
            left_coords = []
            for i in range(steps_half + 1):
                theta = math.pi * 0.5 + (i / steps_half) * math.pi
                px_t, py_t = self._get_track_point(theta, scale)
                left_coords.extend((px_t, py_t))

            right_coords = []
            for i in range(steps_half + 1):
                theta = math.pi * 1.5 + (i / steps_half) * math.pi
                px_t, py_t = self._get_track_point(theta, scale)
                right_coords.extend((px_t, py_t))

            self.create_line(*left_coords, fill=left_glow_col, width=8, capstyle="round", joinstyle="round", tags=("static_rails",))
            self.create_line(*right_coords, fill=right_glow_col, width=8, capstyle="round", joinstyle="round", tags=("static_rails",))
            self.create_line(*left_coords, fill=left_track_col, width=2, capstyle="round", joinstyle="round", tags=("static_rails",))
            self.create_line(*right_coords, fill=right_track_col, width=2, capstyle="round", joinstyle="round", tags=("static_rails",))

        if self.pattern == "figure8":
            a_mid = self.w * 0.22
            left_center_x = cx - a_mid * 0.55
            right_center_x = cx + a_mid * 0.55
            self.create_text(left_center_x - 6, cy, text="(", fill=left_track_col, font=("Segoe UI", 26, "bold"), tags=("static_rails",))
            self.create_text(left_center_x + 6, cy, text=")", fill=ACCENT_PURPLE, font=("Segoe UI", 26, "bold"), tags=("static_rails",))
            self.create_text(left_center_x, cy, text="∞", fill=left_track_col, font=("Segoe UI", 24, "bold"), tags=("static_rails",))
            ret_r = 16
            ret_center_col = ACCENT_GOLD if gold_reticle else ACCENT_CYAN
            self.create_line(right_center_x - 9, cy, right_center_x + 9, cy, fill=ret_center_col, width=1.5, tags=("static_rails",))
            self.create_line(right_center_x, cy - 9, right_center_x, cy + 9, fill=ret_center_col, width=1.5, tags=("static_rails",))
            for s_deg in (25, 115, 205, 295):
                self.create_arc(right_center_x - ret_r, cy - ret_r, right_center_x + ret_r, cy + ret_r,
                                start=s_deg, extent=40, style="arc", outline=ret_center_col, width=1.5, tags=("static_rails",))
            self.create_line(right_center_x - ret_r - 5, cy, right_center_x - ret_r, cy, fill=ret_center_col, width=1.5, tags=("static_rails",))
            self.create_line(right_center_x + ret_r, cy, right_center_x + ret_r + 5, cy, fill=ret_center_col, width=1.5, tags=("static_rails",))
            self.create_line(right_center_x, cy - ret_r - 5, right_center_x, cy - ret_r, fill=ret_center_col, width=1.5, tags=("static_rails",))
            self.create_line(right_center_x, cy + ret_r, right_center_x, cy + ret_r + 5, fill=ret_center_col, width=1.5, tags=("static_rails",))
        else:
            self.create_text(cx, cy - 8, text="⟷", fill=ACCENT_CYAN, font=("Segoe UI", 28, "bold"), tags=("static_rails",))
            self.create_text(cx, cy + 18, text="SMOOTH PURSUIT SACCADES", fill=TEXT_MUTED, font=("Segoe UI", 10, "bold"), tags=("static_rails",))
            self.create_text(cx - self.w * 0.34 + 20, cy, text="◂ LEFT", fill=left_track_col, font=("Segoe UI", 10, "bold"), tags=("static_rails",))
            self.create_text(cx + self.w * 0.34 - 20, cy, text="RIGHT ▸", fill=right_track_col, font=("Segoe UI", 10, "bold"), tags=("static_rails",))

        node_theta = 1.28 * math.pi if self.pattern == "figure8" else math.pi
        node_x, node_y = self._get_track_point(node_theta, scale=1.0)
        self.create_oval(node_x - 4, node_y - 4, node_x + 4, node_y + 4, fill="#FFFFFF", outline=left_track_col, width=1, tags=("static_rails",))
        self.create_line(node_x, node_y + 4, node_x, node_y + 26, fill=TEXT_SECONDARY, width=1, tags=("static_rails",))
        self.create_line(node_x, node_y + 26, node_x + 40, node_y + 26, fill=TEXT_SECONDARY, width=1, tags=("static_rails",))
        routine_lbl = "Gamified Figure-8\nEye Gymnastics" if self.pattern == "figure8" else "Horizontal Smooth\nPursuit Workout"
        self.create_text(node_x + 44, node_y + 26, text=routine_lbl, fill=TEXT_SECONDARY, font=("Segoe UI", 10), anchor="w", tags=("static_rails",))
        self._rails_drawn = True

    def _draw(self):
        # Item 5: Draw gym rails once and redraw only moving parts
        lvl = getattr(self.master_app, '_player_level', 1) if self.master_app else 1
        scale_key = (self.w, self.h, self.pattern, lvl)
        if not getattr(self, '_rails_drawn', False) or getattr(self, '_cached_scale_key', None) != scale_key:
            self._cached_scale_key = scale_key
            self._draw_static_rails()

        self.delete("moving")
        cx, cy = self.w / 2, self.h / 2

        streak = getattr(self.master_app, '_streak', lambda: 1)() if self.master_app else 1
        has_face = getattr(self.master_app, '_face_present', False) if self.master_app else True
        gold_reticle = (lvl >= 3)
        zen_breath = (lvl >= 4)
        emerald_active = (lvl >= 2)
        left_track_col = "#10B981" if emerald_active else ACCENT_CYAN

        # ── 1. Top Badges Row (Telemetry matching Mockup Image 2 & 4) ─────────
        pill_y = 20
        px = 20
        acc_txt = f"{int(self.accuracy)}% Accuracy" if self.has_tracked and has_face else "--% Tracking"
        px = self._draw_pill(px, pill_y, acc_txt, ACCENT_CYAN, "#0284C7", "#05233A")
        px = self._draw_pill(px, pill_y, f"Streak x{streak}", ACCENT_GREEN, "#059669", "#042B1F")
        xp_pill_txt = f"+{self.last_awarded_xp} XP"
        px = self._draw_pill(px, pill_y, xp_pill_txt, ACCENT_PURPLE, "#7C3AED", "#2A0E4E")

        # ── 3. Traced Path Energy Beam (Illuminates progress along circuit) ───
        if self.t > 0.05:
            traced_steps = max(6, int((self.t / (2 * math.pi)) * 60))
            traced_coords = []
            for i in range(traced_steps + 1):
                theta_t = (i / traced_steps) * self.t
                tx, ty = self._get_track_point(theta_t, scale=1.0)
                traced_coords.extend((tx, ty))

            if len(traced_coords) >= 4:
                self.create_line(*traced_coords, fill="#FFFFFF", width=3, capstyle="round", joinstyle="round", tags=("moving",))

        # ── 5. Target Orb & Particle Stardust Trail ───────────────────────────
        orb_x, orb_y = self._get_track_point(self.t, scale=1.0)
        self.particles.append((orb_x, orb_y))

        for idx, (tx, ty) in enumerate(self.particles):
            p_rad = 0.8 + (idx * 0.30)
            p_col = left_track_col if idx % 2 == 0 else "#FFFFFF"
            self.create_oval(tx - p_rad, ty - p_rad, tx + p_rad, ty + p_rad, fill=p_col, outline="", tags=("moving",))

        # Glowing Target Orb Nucleus & Halo
        orb_halo_r = 14 + math.sin(time.monotonic() * 5.0) * 2.5
        orb_halo_col = left_track_col if orb_x < cx else ACCENT_PURPLE
        self.create_oval(orb_x - orb_halo_r, orb_y - orb_halo_r, orb_x + orb_halo_r, orb_y + orb_halo_r,
                         outline=orb_halo_col, width=1.5, tags=("moving",))
        self.create_oval(orb_x - 7, orb_y - 7, orb_x + 7, orb_y + 7,
                         fill="#FFFFFF", outline=orb_halo_col, width=2, tags=("moving",))

        # ── 6. Leader Lines & Annotations ─────────────────────────────────────
        lead1_x, lead1_y = orb_x, orb_y
        self.create_line(lead1_x + 8, lead1_y - 8, lead1_x + 28, lead1_y - 24, fill=TEXT_SECONDARY, width=1, tags=("moving",))
        self.create_line(lead1_x + 28, lead1_y - 24, lead1_x + 75, lead1_y - 24, fill=TEXT_SECONDARY, width=1, tags=("moving",))
        self.create_text(lead1_x + 80, lead1_y - 24, text="Gaze-tracking\nlock-on",
                         fill=TEXT_SECONDARY, font=("Segoe UI", 10), anchor="w", tags=("moving",))

        # ── 7. Damped User Gaze Cursor & Real-Time Sync Indicator ─────────────
        rx, ry = self.user_x, self.user_y
        dist_to_orb = math.hypot(rx - orb_x, ry - orb_y)

        if gold_reticle:
            ret_col = ACCENT_GOLD if self.locked else (ACCENT_AMBER if dist_to_orb < 80 else "#D97706")
        else:
            ret_col = ACCENT_GREEN if self.locked else (ACCENT_CYAN if dist_to_orb < 80 else ACCENT_AMBER)

        self.create_oval(rx - 8, ry - 8, rx + 8, ry + 8, outline=ret_col, width=1.5, tags=("moving",))
        self.create_oval(rx - 2, ry - 2, rx + 2, ry + 2, fill=ret_col, outline="", tags=("moving",))
        self.create_line(rx - 13, ry, rx - 6, ry, fill=ret_col, width=1.5, tags=("moving",))
        self.create_line(rx + 6, ry, rx + 13, ry, fill=ret_col, width=1.5, tags=("moving",))
        self.create_line(rx, ry - 13, rx, ry - 6, fill=ret_col, width=1.5, tags=("moving",))
        self.create_line(rx, ry + 6, rx, ry + 13, fill=ret_col, width=1.5, tags=("moving",))

        if not self.locked and has_face:
            self.create_text(cx, self.h - 14, text="🎯 Follow the neon orb with your gaze to trace the circuit and earn XP",
                             fill=TEXT_MUTED, font=("Segoe UI", 10, "italic"), tags=("moving",))

        if zen_breath:
            now_sec = time.monotonic() % 8.0
            is_inhale = (now_sec < 4.0)
            phase_prog = (now_sec / 4.0) if is_inhale else ((now_sec - 4.0) / 4.0)
            breath_rad = 5 + int((phase_prog if is_inhale else (1.0 - phase_prog)) * 8)
            b_txt = f"🧘 Zen Breath: {'Inhale' if is_inhale else 'Exhale'}... ({4.0 - (now_sec % 4.0):.1f}s)"
            self.create_oval(cx - breath_rad, cy + self.h * 0.28 - breath_rad, cx + breath_rad, cy + self.h * 0.28 + breath_rad,
                             outline=ACCENT_CYAN, width=1, tags=("moving",))
            self.create_text(cx, cy + self.h * 0.28 + 16, text=b_txt, fill=TEXT_MUTED, font=("Segoe UI", 10, "bold"), tags=("moving",))


# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-FIDELITY CANVAS 3: Daily Wellness Rings (Cyberpunk Luminous Bloom)
# ══════════════════════════════════════════════════════════════════════════════
class ConcentricRingsCanvas(ctk.CTkCanvas):
    """
    Renders three thick, desaturated glowing Cyberpunk activity rings (1:1 Exact Replica):
      - Outer Ring: Muted Cyan (Blinks)
      - Middle Ring: Muted Purple (Breaks)
      - Inner Ring: Muted Green (Posture)
      - Native smooth rounded caps via capstyle=tk.ROUND
      - Subtle neon bloom shadow under core arc
      - Dark desaturated tinted 360-degree background tracks (#08182D, #160B2A, #041C11)
    """
    def __init__(self, master, size=240, **kwargs):
        super().__init__(master, width=size, height=size, bg=BG_CARD, highlightthickness=0, **kwargs)
        self.size = size
        self.blink_pct = 0.0
        self.break_pct = 0.0
        self.posture_pct = 0.0
        self.bind("<Configure>", self._on_configure)
        self._draw()

    def create_arc(self, *args, **kwargs):
        # Gracefully translate arc with capstyle="round" / tk.ROUND into a smooth circular path with true rounded caps
        capstyle = kwargs.pop("capstyle", None)
        style = kwargs.get("style", "pieslice")
        if style == "arc" and capstyle in (tk.ROUND, "round"):
            if len(args) == 4:
                x0, y0, x1, y1 = args
            elif len(args) == 1 and len(args[0]) == 4:
                x0, y0, x1, y1 = args[0]
            else:
                x0 = kwargs.get("x0", 0)
                y0 = kwargs.get("y0", 0)
                x1 = kwargs.get("x1", 0)
                y1 = kwargs.get("y1", 0)

            cx = (x0 + x1) / 2.0
            cy = (y0 + y1) / 2.0
            rx = abs(x1 - x0) / 2.0
            ry = abs(y1 - y0) / 2.0

            start_deg = kwargs.get("start", 0)
            extent_deg = kwargs.get("extent", 90)
            width = kwargs.get("width", 1)
            color = kwargs.get("outline", "black")

            # Interpolate smooth points along the circle
            num_steps = max(16, int(abs(extent_deg) / 2.0))
            pts = []
            for i in range(num_steps + 1):
                ang = math.radians(start_deg + (extent_deg * i / num_steps))
                px = cx + rx * math.cos(ang)
                py = cy - ry * math.sin(ang)
                pts.extend([px, py])

            return self.create_line(pts, width=width, fill=color, capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)
        else:
            return super().create_arc(*args, **kwargs)

    def _on_configure(self, event):
        if event.width > 50 and event.height > 50:
            new_size = min(event.width, event.height)
            if new_size != self.size:
                self.size = new_size
                self._draw()

    def set_metrics(self, b_pct: float, br_pct: float, p_pct: float):
        self.blink_pct = min(1.0, max(0.0, float(b_pct)))
        self.break_pct = min(1.0, max(0.0, float(br_pct)))
        self.posture_pct = min(1.0, max(0.0, float(p_pct)))
        self._draw()

    def _draw(self):
        self.delete("all")
        cx = self.size / 2.0
        cy = self.size / 2.0

        # Exact proportional radii for size=240:
        scale = self.size / 240.0
        r_outer = 94.0 * scale
        r_mid   = 72.0 * scale
        r_inner = 50.0 * scale
        track_w = 15.0 * scale
        glow_w  = 21.0 * scale

        # Rings configuration: (radius, pct, active_color, bloom_shadow_color, dark_desaturated_track)
        # Outer = Muted Cyan, Middle = Muted Purple, Inner = Muted Green
        rings = [
            (r_outer, self.blink_pct,   ACCENT_CYAN,   "#0A3A5E", "#08182D"),  # Outer: Cyan (Blinks)
            (r_mid,   self.break_pct,   ACCENT_PURPLE, "#4A1A70", "#160B2A"),  # Middle: Purple (Breaks)
            (r_inner, self.posture_pct, ACCENT_GREEN,  "#084832", "#041C11")   # Inner: Green (Posture)
        ]

        for radius, pct, active_color, bloom_color, track_color in rings:
            # 1. Dark desaturated background track
            self.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                outline=track_color, width=track_w
            )

            if pct > 0.01:
                extent = -360.0 * pct

                # 2. Desaturated bloom glow shadow beneath main arc
                self.create_arc(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    start=90, extent=extent, style="arc",
                    width=glow_w, outline=bloom_color, capstyle="round"
                )

                # 3. Active bright arc directly on top
                self.create_arc(
                    cx - radius, cy - radius, cx + radius, cy + radius,
                    start=90, extent=extent, style="arc",
                    width=track_w, outline=active_color, capstyle="round"
                )


# ══════════════════════════════════════════════════════════════════════════════
#  StatusCard & LabeledSlider
# ══════════════════════════════════════════════════════════════════════════════
class StatusCard(ctk.CTkFrame):
    STATES = {"standby": ACCENT_AMBER, "active": ACCENT_GREEN, "error": ACCENT_RED, "offline": TEXT_MUTED}

    def __init__(self, master, label: str = "Status", value: str = "Standby", **kwargs):
        super().__init__(master, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                         border_width=1, border_color=BORDER_CARD, **kwargs)
        self._current_color = ACCENT_AMBER
        self._flash_job = None
        self._last_val = ""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(self, text="●", font=ctk.CTkFont(size=18), text_color=self._current_color, width=32)
        self._dot.grid(row=0, column=0, padx=(14, 4), pady=12, sticky="w")

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=1, padx=(0, 14), pady=8, sticky="ew")

        ctk.CTkLabel(text_frame, text=label.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED, anchor="w").pack(anchor="w")
        self._value_lbl = ctk.CTkLabel(text_frame, text=value, font=ctk.CTkFont(size=14, weight="bold"),
                                       text_color=TEXT_PRIMARY, anchor="w")
        self._value_lbl.pack(anchor="w")

    def set_status(self, value: str, color: str = None):
        if color is None: color = self.STATES.get(value.lower(), ACCENT_AMBER)
        if self._last_val == value and self._current_color == color: return
        self._last_val = value
        def _update():
            self._value_lbl.configure(text=value)
            self._dot.configure(text_color=color)
            self._current_color = color
        self.after(0, _update)

    def flash(self, color: str = ACCENT_RED, duration_ms: int = 300):
        original = self._current_color
        def _restore():
            self._dot.configure(text_color=original)
            self._current_color = original
        self.after(0, lambda: self._dot.configure(text_color=color))
        self.after(0, lambda: setattr(self, '_current_color', color))
        if self._flash_job: self.after_cancel(self._flash_job)
        self._flash_job = self.after(duration_ms, _restore)


class LabeledSlider(ctk.CTkFrame):
    def __init__(self, master, title: str, from_: float, to: float, initial: float, fmt: str = ".2f", command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._fmt, self._user_command = fmt, command
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_SECONDARY, anchor="w").grid(row=0, column=0, sticky="w", padx=2)
        self._val_lbl = ctk.CTkLabel(self, text=format(initial, fmt), font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color=ACCENT_CYAN, width=50, anchor="e")
        self._val_lbl.grid(row=0, column=1, sticky="e", padx=2)
        
        self._slider = ctk.CTkSlider(
            self, from_=from_, to=to, number_of_steps=max(1, int((to - from_) / 0.01)),
            button_color=ACCENT_CYAN, button_hover_color=ACCENT_BLUE,
            progress_color=ACCENT_CYAN, fg_color=BG_SURFACE, command=self._on_change
        )
        self._slider.set(initial)
        self._slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    def _on_change(self, value: float):
        self._val_lbl.configure(text=format(value, self._fmt))
        if self._user_command: self._user_command(value)

    def set_value(self, value: float):
        self._slider.set(value)
        self._val_lbl.configure(text=format(value, self._fmt))

# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-FIDELITY CANVAS 4: Interactive Dwell Calibration & Practice Sandbox
# ══════════════════════════════════════════════════════════════════════════════
class DwellSandboxCanvas(ctk.CTkCanvas):
    """
    Interactive Dwell Calibration & Target Practice Sandbox.
    Matches the real dwell engine: tests 'stay within the radius of where you stopped'.
    Accumulates dwell progress continuously in _animate() so holding perfectly still
    advances the timer and registers hits smoothly.
    """
    def __init__(self, master, width=380, height=135, **kwargs):
        super().__init__(master, width=width, height=height, bg=BG_CARD_INNER, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.hits = 0
        self.dwell_time = 1.0
        self.dwell_radius = 25
        self._hover_start = None
        self._progress = 0.0
        self._anchor_x = None
        self._anchor_y = None
        self._curr_mouse_x = None
        self._curr_mouse_y = None
        self._just_hit = False
        self._hit_flash_t = 0
        self._last_hit_pos = None
        
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<Configure>", self._on_configure)
        self._animate()

    def _on_configure(self, event):
        if event.width > 50 and event.height > 50:
            self.w, self.h = event.width, event.height
            self._draw()

    def set_params(self, dwell_time, dwell_radius):
        self.dwell_time = max(0.2, float(dwell_time))
        self.dwell_radius = max(10, int(dwell_radius))
        self._draw()

    def reset_hits(self):
        self.hits = 0
        self._hover_start = None
        self._progress = 0.0
        self._anchor_x = None
        self._anchor_y = None
        self._just_hit = False
        self._hit_flash_t = 0
        self._last_hit_pos = None
        self._draw()

    def _on_mouse_enter(self, event):
        self._curr_mouse_x = event.x
        self._curr_mouse_y = event.y

    def _on_mouse_move(self, event):
        self._curr_mouse_x = event.x
        self._curr_mouse_y = event.y

    def _on_mouse_leave(self, event):
        self._curr_mouse_x = None
        self._curr_mouse_y = None
        self._anchor_x = None
        self._anchor_y = None
        self._hover_start = None
        self._progress = 0.0
        self._just_hit = False
        self._draw()

    def _animate(self):
        if not self.winfo_viewable():
            self.after(100, self._animate)
            return
        now = time.monotonic()
        if self._curr_mouse_x is not None and self._curr_mouse_y is not None:
            # Mouse is inside sandbox: check distance to stopping anchor
            if self._anchor_x is None:
                self._anchor_x = self._curr_mouse_x
                self._anchor_y = self._curr_mouse_y
                self._hover_start = now
                self._progress = 0.0
                self._just_hit = False
            else:
                dist = math.hypot(self._curr_mouse_x - self._anchor_x, self._curr_mouse_y - self._anchor_y)
                if dist > self.dwell_radius:
                    # Moved beyond tolerance radius: reset anchor point to where cursor stopped
                    self._anchor_x = self._curr_mouse_x
                    self._anchor_y = self._curr_mouse_y
                    self._hover_start = now
                    self._progress = 0.0
                    self._just_hit = False
                else:
                    # Within radius of stopping point: progress accumulates even if 100% still!
                    elapsed = now - (self._hover_start or now)
                    self._progress = min(1.0, elapsed / max(0.1, self.dwell_time))
                    if self._progress >= 1.0 and not self._just_hit:
                        self.hits += 1
                        self._just_hit = True
                        self._hit_flash_t = 12
                        self._last_hit_pos = (self._anchor_x, self._anchor_y)
                        self._hover_start = now

        if self._hit_flash_t > 0:
            self._hit_flash_t -= 1

        self._draw()
        self.after(30, self._animate)

    def _draw(self):
        self.delete("all")
        # Center anchor fallback if no mouse inside
        cx = self._anchor_x if self._anchor_x is not None else (self.w / 2)
        cy = self._anchor_y if self._anchor_y is not None else (self.h / 2)
        r = self.dwell_radius
        
        # Subtle guide crosshairs at center
        mid_x, mid_y = self.w / 2, self.h / 2
        self.create_line(12, mid_y, self.w - 12, mid_y, fill="#162238", width=1, dash=(2, 4))
        self.create_line(mid_x, 10, mid_x, self.h - 10, fill="#162238", width=1, dash=(2, 4))
        
        # Corner brackets
        pad = 8
        self.create_line(pad, pad + 10, pad, pad, pad + 10, pad, fill=BORDER_CARD, width=1)
        self.create_line(self.w - pad - 10, pad, self.w - pad, pad, self.w - pad, pad + 10, fill=BORDER_CARD, width=1)
        self.create_line(pad, self.h - pad - 10, pad, self.h - pad, pad + 10, self.h - pad, fill=BORDER_CARD, width=1)
        self.create_line(self.w - pad - 10, self.h - pad, self.w - pad, self.h - pad, self.w - pad, self.h - pad - 10, fill=BORDER_CARD, width=1)
        
        # Target outer boundary (anchor radius)
        border_col = ACCENT_GREEN if self._hit_flash_t > 0 else (ACCENT_AMBER if self._progress > 0 else BORDER_CARD)
        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=border_col, width=1, dash=(4, 3))
        
        # Circular Dwell Progress Arc
        if self._progress > 0.01:
            extent = -360.0 * self._progress
            self.create_arc(cx - r, cy - r, cx + r, cy + r, start=90, extent=extent,
                            style="arc", outline=ACCENT_CYAN, width=3)
            # Center charging core
            inner_r = max(4, int(r * self._progress * 0.7))
            self.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                             fill=ACCENT_CYAN, outline="")
        else:
            pip_col = ACCENT_GREEN if self._hit_flash_t > 0 else (ACCENT_CYAN if self._curr_mouse_x is not None else TEXT_MUTED)
            self.create_oval(cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5, fill=pip_col, outline="")

        # Current mouse cursor pip if inside
        if self._curr_mouse_x is not None and self._curr_mouse_y is not None:
            mx, my = self._curr_mouse_x, self._curr_mouse_y
            self.create_oval(mx - 2, my - 2, mx + 2, my + 2, fill=ACCENT_CYAN, outline="")
            
        # Target hit celebration flash ring
        if self._hit_flash_t > 0:
            fx, fy = self._last_hit_pos if self._last_hit_pos else (cx, cy)
            burst_r = r + (12 - self._hit_flash_t) * 3
            self.create_oval(fx - burst_r, fy - burst_r, fx + burst_r, fy + burst_r,
                             outline=ACCENT_GREEN, width=2)
            self.create_text(fx, max(16, fy - r - 12), text="★ DWELL TRIGGERED!", fill=ACCENT_GREEN,
                             font=("Segoe UI", 10, "bold"))
        else:
            if self._curr_mouse_x is None:
                hint_txt = "Move mouse here and pause to test dwell"
                hint_col = TEXT_MUTED
            elif self._progress > 0:
                rem = max(0.0, self.dwell_time * (1.0 - self._progress))
                hint_txt = f"Holding still... {int(self._progress * 100)}% ({rem:.1f}s)"
                hint_col = ACCENT_CYAN
            else:
                hint_txt = "Hold still to charge dwell"
                hint_col = TEXT_SECONDARY
            self.create_text(mid_x, mid_y - r - 14, text=hint_txt, fill=hint_col,
                             font=("Segoe UI", 10, "bold"))
            
        # Stats readouts in corners
        self.create_text(16, 14, text=f"Hits Registered: {self.hits}", fill=TEXT_PRIMARY,
                         font=("Consolas", 9, "bold"), anchor="w")
        self.create_text(self.w - 16, 14, text=f"Dwell: {self.dwell_time:.2f}s  ·  ±{r}px", fill=TEXT_SECONDARY,
                         font=("Consolas", 9), anchor="e")


# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-FIDELITY CANVAS 5: Smart Scroll 3-Zone Altitude Radar
# ══════════════════════════════════════════════════════════════════════════════
class ScrollRadarCanvas(ctk.CTkCanvas):
    """
    Visual 3-Zone Smart Scroll Diagram & Real-Time Head Altitude Radar.
    Shows the three trigger zones (Up, Deadzone, Down) with a live position beacon.
    """
    def __init__(self, master, width=380, height=135, **kwargs):
        super().__init__(master, width=width, height=height, bg=BG_CARD_INNER, highlightthickness=0, **kwargs)
        self.w, self.h = width, height
        self.altitude = 0.5  # 0.0 (top) to 1.0 (bottom)
        self.bind("<Configure>", self._on_configure)
        self._draw()

    def _on_configure(self, event):
        if event.width > 50 and event.height > 50:
            self.w, self.h = event.width, event.height
            self._draw()

    def set_altitude(self, alt: float):
        clamped = max(0.0, min(1.0, float(alt)))
        if abs(clamped - self.altitude) > 0.008:
            self.altitude = clamped
            self._draw()

    def _draw(self):
        self.delete("all")
        pad = 10
        rw = self.w - (pad * 2)
        rh = self.h - (pad * 2)
        
        top_h = rh * 0.35
        mid_h = rh * 0.30
        bot_h = rh * 0.35
        
        y0 = pad
        y1 = y0 + top_h
        y2 = y1 + mid_h
        y3 = y2 + bot_h
        
        # 1. Zone 1: Top Scroll Zone (<35%)
        in_top = self.altitude < 0.35
        top_col = "#0C334D" if in_top else "#091D2C"
        top_border = ACCENT_CYAN if in_top else "#143750"
        self.create_rectangle(pad, y0, pad + rw, y1, fill=top_col, outline=top_border, width=1)
        self.create_text(pad + 14, y0 + top_h / 2, text="▲  SCROLL UP ZONE  (<35% Screen)",
                         fill=ACCENT_CYAN if in_top else TEXT_SECONDARY, font=("Segoe UI", 10, "bold"), anchor="w")
        
        # 2. Zone 2: Neutral Deadzone (35% - 65%)
        in_mid = 0.35 <= self.altitude <= 0.65
        mid_col = "#0B1527" if in_mid else "#080F1E"
        mid_border = ACCENT_BLUE if in_mid else BORDER_CARD
        self.create_rectangle(pad, y1, pad + rw, y2, fill=mid_col, outline=mid_border, width=1)
        self.create_text(pad + 14, y1 + mid_h / 2, text="⏸  NEUTRAL REST DEADZONE  (Cursor Navigation)",
                         fill=TEXT_PRIMARY if in_mid else TEXT_MUTED, font=("Segoe UI", 10, "bold"), anchor="w")
        
        # 3. Zone 3: Bottom Scroll Zone (>65%)
        in_bot = self.altitude > 0.65
        bot_col = "#0C334D" if in_bot else "#091D2C"
        bot_border = ACCENT_CYAN if in_bot else "#143750"
        self.create_rectangle(pad, y2, pad + rw, y3, fill=bot_col, outline=bot_border, width=1)
        self.create_text(pad + 14, y2 + bot_h / 2, text="▼  SCROLL DOWN ZONE  (>65% Screen)",
                         fill=ACCENT_CYAN if in_bot else TEXT_SECONDARY, font=("Segoe UI", 10, "bold"), anchor="w")
        
        # Live Altitude Beacon Pointer
        beacon_y = y0 + (self.altitude * rh)
        beacon_x = pad + rw - 24
        b_col = ACCENT_CYAN if (in_top or in_bot) else ACCENT_GREEN
        self.create_oval(beacon_x - 6, beacon_y - 6, beacon_x + 6, beacon_y + 6, fill=b_col, outline="#FFFFFF", width=1)
        self.create_line(pad + rw - 44, beacon_y, beacon_x - 8, beacon_y, fill=b_col, width=1, dash=(2, 2))
        status_tag = "UP" if in_top else ("DOWN" if in_bot else "REST")
        self.create_text(pad + rw - 50, beacon_y, text=f"GAZE: {status_tag}", fill=b_col,
                         font=("Consolas", 8, "bold"), anchor="e")


# ══════════════════════════════════════════════════════════════════════════════
#  Vision360App (Master Desktop Application with Target EyeRest Layout)
# ══════════════════════════════════════════════════════════════════════════════
class Vision360App(ctk.CTk):
    WINDOW_TITLE  = "Vision360  ·  Hands-Free & Digital Wellness Studio"
    WINDOW_MIN_W  = 1240
    WINDOW_MIN_H  = 780

    def __init__(self):
        super().__init__()
        self.title(self.WINDOW_TITLE)
        self.minsize(self.WINDOW_MIN_W, self.WINDOW_MIN_H)
        self.configure(fg_color=BG_VOID)
        self._center_window(1280, 820)

        # ── State Variables ──────────────────────────────────────────────────
        self._mouse_enabled   = ctk.BooleanVar(value=False)
        self._sensitivity     = 0.25
        self._smoothing       = 0.5
        self._mouth_thresh    = 0.40  
        self._dock_pos_x      = 0.85 
        self._scroll_speed    = 360 
        self._is_dragging     = False
        self._click_mode      = ctk.StringVar(value="Left")
        self._click_mode.trace_add("write", self._on_mode_change)
        self._dwell_time      = 1.0
        self._dwell_radius    = 25
        self._cursor_proj_x   = 0
        self._cursor_proj_y   = 0
        self._norm_head_x     = 0.5
        self._norm_head_y     = 0.5
        self._neutral_x       = 0.5
        self._neutral_y       = 0.5
        self._raw_nose_x      = 0.5
        self._raw_nose_y      = 0.5
        self._nose_history    = collections.deque(maxlen=20)
        self._frame_times     = collections.deque(maxlen=30)
        self._real_fps        = 30.0
        self._tremor_stab_pct = 98.5
        self._ambient_lum     = None
        self._ambient_lux     = None
        self._is_mouth_open   = False
        self._nose_centered   = True

        # ── Thread-safe bridge between the camera thread and Tk ──────────────
        # The camera thread must NEVER touch Tk (variables, widgets, .after()).
        # It reads plain-Python mirrors of the UI state and hands results back
        # through the two channels below, which the main thread drains.
        self._mouse_on        = False                 # mirror of self._mouse_enabled
        self._mode_name       = "Left"                # mirror of self._click_mode
        self._ui_events       = queue.Queue()         # discrete events (toggle, mode reset)
        self._status_lock     = threading.Lock()
        self._pending_status  = None                  # latest (text, color), last-write-wins
        self._pending_flash   = None                  # latest (color, duration_ms)
        
        # ── User Profile & Gamification State (Multi-User Workstation Support) ─
        self._profile_path     = user_data_dir() / "vision360_profile.json"
        self._profiles_path    = user_data_dir() / "vision360_profiles.json"
        self._profiles_db      = {"active_id": "default", "profiles": {}}
        self._active_profile_id = "default"
        self._switcher_dialog   = None
        self._load_profile()          # sets name / xp / level / streak / lifetime stats
        self._total_clicks     = 0
        
        # ── Digital Wellness State ───────────────────────────────────────────
        self._current_tab         = "🫀 EyeRest"
        self._session_start       = time.time()
        # None = "no reading yet" (still measuring, or no face on camera).
        self._current_bpm         = None
        self._current_dist_cm     = None
        self._face_present        = False
        self._latency_ms          = None
        self._last_sync_t         = None
        self._last_rings          = None
        
        # Real-time posture analytics (seconds of face-on-camera time)
        self._posture_good_secs   = 0.0
        self._posture_total_secs  = 0.0
        self._session_blinks      = 0     # blinks counted this run (thread increments)
        self._hands_free_secs     = 0.0   # time with mouse control ON this run
        
        self._current_tilt_deg    = 0.0
        self._turtle_neck         = False
        self._away_gazes_done     = self._loaded_breaks   # today's cycles, restored from the profile
        self._break_interval_mins = 20.0
        self._cycle_20_20         = 20 * 60.0
        
        # ── Camera & Threading ───────────────────────────────────────────────
        self._cam_thread      = None
        self._cam_running     = False
        self._frame_queue     = queue.Queue(maxsize=2)
        self._camera_live     = False

        # ── Presentation Mode & Feature Guide Dialog State ───────────────────
        self._floating_face_cam = None
        self._floating_cam_var  = ctk.BooleanVar(value=False)
        self._active_cap = None
        self._feature_guide_dialog = None

        # Build UI Architecture
        self._build_layout()
        self._start_session_timer()
        self._start_wellness_cycle()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(300, self._start_camera)

    def _center_window(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _on_mode_change(self, *args):
        if not self._click_mode.get():
            self._click_mode.set("Left")
        mode = self._click_mode.get()
        self._mode_name = mode
        
        if mode == "Type":
            if not hasattr(self, 'keyboard') or not self.keyboard.winfo_exists():
                self.keyboard = VirtualKeyboard(self, lambda: self._click_mode.set("Left"))
        else:
            if hasattr(self, 'keyboard') and self.keyboard.winfo_exists():
                self.keyboard.destroy()
                
        if hasattr(self, 'dock') and self.dock.winfo_exists():
            self.dock.update_styles()
        if hasattr(self, 'mode_pill_dock'):
            self._update_quick_dock_styles()

    # ──────────────────────────────────────────────────────────────────────────
    #  Main Layout: Left Sidebar + Top Studio Header + Main Canvas + Telemetry
    # ──────────────────────────────────────────────────────────────────────────
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=226)  # Left Sidebar Card
        self.grid_columnconfigure(1, weight=1)                # Main Stage
        self.grid_rowconfigure(0, weight=1)                   # Body
        self.grid_rowconfigure(1, weight=0)                   # Bottom Telemetry

        self._build_sidebar()
        self._build_main_stage()
        self._build_bottom_telemetry_hud()

    # ──────────────────────────────────────────────────────────────────────────
    #  Left Sidebar Navigation Rail & Brand Header
    # ──────────────────────────────────────────────────────────────────────────
    def _load_brand_logo(self, size=(28, 28)):
        """Safely loads user's uploaded Vision360 logo image if Pillow is available."""
        if Image is None:
            return None
        candidate_paths = [
            str(resource_path("vision360_logo.png")),
            str(resource_path("image_c6369846.png")),
            "vision360_logo.png",
            "image_c6369846.png",
            os.path.join(os.getcwd(), "public", "assets", "aistudio", "vision360_logo.png"),
            os.path.join(os.getcwd(), "public", "assets", "aistudio", "image_c6369846.png"),
        ]
        for p in candidate_paths:
            if os.path.isfile(p):
                try:
                    pil_img = Image.open(p)
                    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                except Exception:
                    pass
        return None

    def _toggle_sidebar(self):
        """Collapses or expands the left workspace sidebar so Vision360 workspace can slide full-screen."""
        if not hasattr(self, 'sidebar'):
            return
        self._sidebar_visible = not getattr(self, '_sidebar_visible', True)
        if self._sidebar_visible:
            self.grid_columnconfigure(0, weight=0, minsize=226)
            self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=(10, 8))
            if hasattr(self, 'btn_expand_sidebar'):
                self.btn_expand_sidebar.pack_forget()
        else:
            self.sidebar.grid_remove()
            self.grid_columnconfigure(0, weight=0, minsize=0)
            if hasattr(self, 'btn_expand_sidebar'):
                self.btn_expand_sidebar.pack(side="left", padx=(0, 10))

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=BORDER_CARD,
            width=210
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=(10, 8))
        sidebar.grid_propagate(False)
        self.sidebar = sidebar
        self._sidebar_visible = True

        # Brand Header (App name: VISION360 with uploaded logo beside it)
        brand_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_box.pack(fill="x", padx=16, pady=(16, 14))
        
        # Load user uploaded logo safely beside VISION360
        self._brand_logo_img = self._load_brand_logo(size=(28, 28))
        if self._brand_logo_img is not None:
            logo = ctk.CTkLabel(brand_box, image=self._brand_logo_img, text="")
            logo.pack(side="left", padx=(0, 8))
        else:
            logo = ctk.CTkLabel(brand_box, text="◈", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_CYAN)
            logo.pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(brand_box, text="VISION360", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")

        # Navigation Menu Header with Collapse Toggle Button
        ws_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        ws_header.pack(fill="x", padx=18, pady=(0, 6))

        ctk.CTkLabel(ws_header, text="WORKSPACE", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
        
        self.btn_collapse_sidebar = ctk.CTkButton(
            ws_header, text="◀", width=22, height=20, corner_radius=6,
            fg_color=BG_CARD_INNER, hover_color=BG_SURFACE, text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self._toggle_sidebar
        )
        self.btn_collapse_sidebar.pack(side="right")
        
        self.sidebar_buttons = {}
        tabs = [
            ("◈ Cockpit", "Vision Tracking Feed"),
            ("⚙ Motor", "Input & Sensitivity"),
            ("🫀 EyeRest", "Digital Wellness Suite"),
            ("♾ EyeGym", "Figure-8 Gymnastics"),
            ("👤 Profile", "User & Presets")
        ]
        
        for name, sub in tabs:
            btn = ctk.CTkButton(
                sidebar, text=name, font=ctk.CTkFont(size=12, weight="bold"),
                height=40, corner_radius=10, fg_color="transparent", text_color=TEXT_SECONDARY,
                hover_color=BG_SURFACE, anchor="w",
                command=lambda n=name: self._switch_tab(n)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.sidebar_buttons[name] = btn

        # Bottom Mini Profile Pill
        bottom_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=10, pady=12)

        profile_pill = ctk.CTkFrame(bottom_box, fg_color=BG_CARD_INNER, corner_radius=12, border_width=1, border_color=BORDER_SUBTLE)
        profile_pill.pack(fill="x", pady=4)
        
        avatar_lbl = ctk.CTkLabel(profile_pill, text=self._initials(), font=ctk.CTkFont(size=11, weight="bold"),
                                  fg_color=ACCENT_PURPLE, text_color=TEXT_PRIMARY, width=30, height=30, corner_radius=15)
        avatar_lbl.pack(side="left", padx=8, pady=8)
        self.sb_avatar = avatar_lbl
        
        p_info = ctk.CTkFrame(profile_pill, fg_color="transparent")
        p_info.pack(side="left", padx=(0, 4), fill="x", expand=True)
        self.sb_name_lbl = ctk.CTkLabel(p_info, text=self._user_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY, anchor="w")
        self.sb_name_lbl.pack(anchor="w")
        self.sb_level_lbl = ctk.CTkLabel(p_info, text=f"Lvl {self._player_level} · {self._rank_title()}", font=ctk.CTkFont(size=10), text_color=ACCENT_CYAN, anchor="w")
        self.sb_level_lbl.pack(anchor="w")

        # Quick Switch Profile button
        sb_switch_btn = ctk.CTkButton(
            profile_pill, text="⇄", width=26, height=26, corner_radius=13,
            fg_color=BG_SURFACE, hover_color=ACCENT_CYAN, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_profile_switcher
        )
        sb_switch_btn.pack(side="right", padx=6, pady=8)

        # Make entire pill clickable to open Profile Switcher
        for widget in (profile_pill, avatar_lbl, p_info, self.sb_name_lbl, self.sb_level_lbl):
            widget.bind("<Button-1>", lambda e: self._open_profile_switcher())

    # ──────────────────────────────────────────────────────────────────────────
    #  Main Content Stage
    # ──────────────────────────────────────────────────────────────────────────
    def _build_main_stage(self):
        self.stage = ctk.CTkFrame(self, fg_color=BG_VOID, corner_radius=0)
        self.stage.grid(row=0, column=1, sticky="nsew")
        self.stage.grid_rowconfigure(0, weight=0)  # Top Studio Bar
        self.stage.grid_rowconfigure(1, weight=1)  # Tab Stage
        self.stage.grid_columnconfigure(0, weight=1)

        self._build_studio_header()

        self.tab_container = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.tab_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(6, 12))

        self.tab_pages = {}
        self.tab_pages["◈ Cockpit"] = self._build_page_cockpit()
        self.tab_pages["⚙ Motor"] = self._build_page_controls()
        self.tab_pages["🫀 EyeRest"] = self._build_page_wellness_suite()
        self.tab_pages["♾ EyeGym"] = self._build_page_gym()
        self.tab_pages["👤 Profile"] = self._build_page_profile()

        # Display EyeRest as initial default view
        self._switch_tab("🫀 EyeRest")

    def _build_studio_header(self):
        header = ctk.CTkFrame(self.stage, fg_color=BG_CARD, corner_radius=0, height=58)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=16, pady=10, sticky="w")

        # Sidebar Expand Button (appears when sidebar is collapsed)
        self.btn_expand_sidebar = ctk.CTkButton(
            title_box, text="☰", width=28, height=28, corner_radius=8,
            fg_color=BG_CARD_INNER, hover_color=BG_SURFACE, text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_sidebar
        )

        self.header_title = ctk.CTkLabel(title_box, text="EYEREST DIGITAL WELLNESS SUITE // 3D BIOMETRICS",
                                         font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY)
        self.header_title.pack(side="left")

        right_hub = ctk.CTkFrame(header, fg_color="transparent")
        right_hub.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        self.btn_help = ctk.CTkButton(
            right_hub, text="?", width=28, height=28, corner_radius=14,
            fg_color=BG_CARD_INNER, hover_color=BG_ELEVATED, text_color=ACCENT_CYAN,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._open_feature_guide
        )
        self.btn_help.pack(side="left", padx=(0, 12))

        self.latency_badge = ctk.CTkLabel(right_hub, text="● Latency: --", font=ctk.CTkFont(size=10, weight="bold"),
                                          fg_color=BG_CARD_INNER, text_color=TEXT_MUTED, corner_radius=8, padx=10, pady=4)
        self.latency_badge.pack(side="left", padx=(0, 14))

        self.mouse_toggle = ctk.CTkSwitch(
            right_hub, text="Mouse Control", font=ctk.CTkFont(size=12, weight="bold"),
            variable=self._mouse_enabled, command=self.toggle_mouse_event,
            progress_color=ACCENT_GREEN, text_color=TEXT_PRIMARY
        )
        self.mouse_toggle.pack(side="left")

        ctk.CTkFrame(header, fg_color=BORDER_SUBTLE, height=1).place(x=0, rely=1.0, relwidth=1.0, anchor="sw")

    def _switch_tab(self, tab_name):
        self._current_tab = tab_name

        # 1. Update navigation button styles
        for name, btn in self.sidebar_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=BG_ELEVATED, text_color=ACCENT_CYAN)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

        # 2. Pack target page FIRST so geometry is mapped immediately without layout lag
        for name, page in self.tab_pages.items():
            if name == tab_name:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()

        titles = {
            "◈ Cockpit": "COMMAND CENTER // LIVE OPTICAL FEED",
            "⚙ Motor": "MOTOR ENGINE // CALIBRATION & DWELL MATRIX",
            "🫀 EyeRest": "EYEREST DIGITAL WELLNESS SUITE // 3D BIOMETRICS",
            "♾ EyeGym": "FIGURE-8 EYE GYMNASTICS // GAZE SYNCHRONIZATION",
            "👤 Profile": f"USER PROFILE & ERGONOMIC PRESETS // {self._user_name.upper()}"
        }
        self.header_title.configure(text=titles.get(tab_name, tab_name))

        # 3. Refresh live widgets after page is mapped
        if "Profile" in tab_name:
            self._refresh_profile_widgets()
        if "EyeGym" in tab_name:
            self._refresh_gym_widgets()
        if "EyeRest" in tab_name:
            if hasattr(self, 'away_gaze_lbl') and self.away_gaze_lbl.winfo_exists():
                self._set_label(self.away_gaze_lbl, f"Away-Gaze Cycles: {self._away_gazes_done} Completed")
            if hasattr(self, 'stat_breaks_lbl') and self.stat_breaks_lbl.winfo_exists():
                self._set_label(self.stat_breaks_lbl, f"{self._away_gazes_done} / {getattr(self, 'DAILY_BREAK_GOAL', 8)} Cycles")
        if "Cockpit" in tab_name:
            if hasattr(self, 'video_label') and self.video_label.winfo_exists():
                self.video_label.place(relx=0.5, rely=0.5, anchor="center")
                self.video_label.lift()

    # ──────────────────────────────────────────────────────────────────────────
    #  Page 3: EyeRest Digital Wellness Suite
    # ──────────────────────────────────────────────────────────────────────────
    def _build_page_wellness_suite(self):
        page = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)  # 3-Card Grid
        page.grid_rowconfigure(1, weight=0)  # Bottom Telemetry Bar

        # ── 1. The 3-Card Grid ────────────────────────────────────────────────
        cards_grid = ctk.CTkFrame(page, fg_color="transparent")
        cards_grid.grid(row=0, column=0, sticky="nsew")
        cards_grid.grid_columnconfigure(0, weight=3)  # Left: Live 3D Posture Guardian
        cards_grid.grid_columnconfigure(1, weight=5)  # Center: Gamified Figure-8 Eye Gymnastics
        cards_grid.grid_columnconfigure(2, weight=3)  # Right: Daily Wellness Rings & Badges
        cards_grid.grid_rowconfigure(0, weight=1)

        # ── Card 1 (Left): Live 3D Posture Guardian ───────────────────────────
        card_posture = ctk.CTkFrame(cards_grid, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                    border_width=1, border_color=BORDER_CARD)
        card_posture.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        card_posture.grid_rowconfigure(1, weight=1)
        card_posture.grid_columnconfigure(0, weight=1)

        head_p = ctk.CTkFrame(card_posture, fg_color="transparent")
        head_p.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        ctk.CTkLabel(head_p, text="Live 3D Posture Guardian", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(head_p, text="···", font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_SECONDARY).pack(side="right")

        # Responsive 3D wireframe canvas auto-scaling to fill container
        self.posture_canvas = PostureSpineCanvas(card_posture)
        self.posture_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(2, 10))

        # ── Card 2 (Center): Blink-Rate & 20-20-20 Cycle ──────────────────────
        card_bpm = ctk.CTkFrame(cards_grid, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=BORDER_CARD)
        card_bpm.grid(row=0, column=1, sticky="nsew", padx=4)
        card_bpm.grid_columnconfigure(0, weight=1)
        card_bpm.grid_rowconfigure((0, 1), weight=1)
        card_bpm.grid_rowconfigure(2, weight=0)

        # Row 0: Blink Frequency Cyberpunk Meter (expands to fill height)
        f_box = ctk.CTkFrame(card_bpm, fg_color=BG_CARD_INNER, corner_radius=14,
                             border_width=1, border_color=BORDER_CARD)
        f_box.grid(row=0, column=0, sticky="nsew", padx=14, pady=(12, 5))
        self.blink_freq_gauge = CyberpunkGaugeCanvas(f_box, width=220, height=160, gauge_type="bpm", title="Blink Frequency")
        self.blink_freq_gauge.pack(fill="both", expand=True, padx=2, pady=(2, 0))
        
        # Item 7: Live EAR readout & 3-second eyes-open calibration
        calib_row = ctk.CTkFrame(f_box, fg_color="transparent")
        calib_row.pack(fill="x", padx=10, pady=(2, 6))
        self.live_ear_lbl = ctk.CTkLabel(calib_row, text="EAR: -- (Measuring)", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_CYAN)
        self.live_ear_lbl.pack(side="left")
        self.calib_ear_btn = ctk.CTkButton(
            calib_row, text="🎯 Calibrate (3s)", font=ctk.CTkFont(size=10, weight="bold"),
            height=24, width=100, corner_radius=8, fg_color=BG_SURFACE, hover_color=BG_CARD,
            command=self._start_ear_calibration
        )
        self.calib_ear_btn.pack(side="right")

        # Row 1: 20-20-20 Rule Cyberpunk Meter (expands to fill height)
        r_box = ctk.CTkFrame(card_bpm, fg_color=BG_CARD_INNER, corner_radius=14,
                             border_width=1, border_color=BORDER_CARD)
        r_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(5, 6))
        self.rule_2020_gauge = CyberpunkGaugeCanvas(r_box, width=220, height=200, gauge_type="timer", title="20-20-20 Rule")
        self.rule_2020_gauge.pack(fill="both", expand=True, padx=2, pady=2)
        self.rule_2020_gauge.bind("<Button-1>", lambda e: self.trigger_break_now())

        # Row 2: The Blue Slider Container (anchored to bottom)
        cycle_box = ctk.CTkFrame(card_bpm, fg_color=BG_CARD_INNER, corner_radius=14)
        cycle_box.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 10))
        cycle_box.grid_columnconfigure(0, weight=1)

        self.cycle_timer_lbl = ctk.CTkLabel(
            cycle_box, text=f"Next Break in: {int(self._break_interval_mins):02d}m 00s",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_CYAN
        )
        self.cycle_timer_lbl.pack(anchor="w", padx=16, pady=(10, 2))
        self.cycle_timer_lbl.bind("<Button-1>", lambda e: self.trigger_break_now())

        self.away_gaze_lbl = ctk.CTkLabel(
            cycle_box, text=f"Away-Gaze Cycles: {self._away_gazes_done} Completed",
            font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY
        )
        self.away_gaze_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        self.break_timer_slider = LabeledSlider(
            cycle_box, title="Break Interval (Minutes)",
            from_=5, to=60, initial=20, fmt=".0f",
            command=self.on_break_interval_change
        )
        self.break_timer_slider.pack(fill="x", padx=16, pady=(0, 10))

        # ── Card 3 (Right): Daily Wellness Rings & Achievement Badges ─────────
        card_rings = ctk.CTkFrame(cards_grid, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                  border_width=1, border_color=BORDER_CARD)
        card_rings.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        card_rings.grid_columnconfigure(0, weight=1)

        head_r = ctk.CTkFrame(card_rings, fg_color="transparent")
        head_r.pack(fill="x", padx=16, pady=(12, 2))
        ctk.CTkLabel(head_r, text="Daily Wellness Rings", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")

        # Concentric Rings (Cyan, Purple, Green - Desaturated Cyberpunk 240x240)
        self.rings_canvas = ConcentricRingsCanvas(card_rings, size=240)
        self.rings_canvas.pack(pady=(2, 4))

        # Legend with Tiny Color Boxes: Blinks (Cyan), Breaks (Purple), Posture (Green)
        leg_row = ctk.CTkFrame(card_rings, fg_color="transparent")
        leg_row.pack(fill="x", padx=14, pady=(2, 8))
        leg_row.grid_columnconfigure((0, 1, 2), weight=1)

        # Col 0: [■ Cyan] Blinks / Tracking
        c1 = ctk.CTkFrame(leg_row, fg_color="transparent")
        c1.grid(row=0, column=0, sticky="ew")
        h1 = ctk.CTkFrame(c1, fg_color="transparent")
        h1.pack(anchor="center")
        ctk.CTkLabel(h1, text="■", font=ctk.CTkFont(size=10), text_color=ACCENT_CYAN).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(h1, text="Blinks", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(c1, text="Tracking", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack()

        # Col 1: [■ Purple] Breaks / Completed
        c2 = ctk.CTkFrame(leg_row, fg_color="transparent")
        c2.grid(row=0, column=1, sticky="ew")
        h2 = ctk.CTkFrame(c2, fg_color="transparent")
        h2.pack(anchor="center")
        ctk.CTkLabel(h2, text="■", font=ctk.CTkFont(size=10), text_color=ACCENT_PURPLE).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(h2, text="Breaks", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(c2, text="Completed", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack()

        # Col 2: [■ Green] Posture / Uptime
        c3 = ctk.CTkFrame(leg_row, fg_color="transparent")
        c3.grid(row=0, column=2, sticky="ew")
        h3 = ctk.CTkFrame(c3, fg_color="transparent")
        h3.pack(anchor="center")
        ctk.CTkLabel(h3, text="■", font=ctk.CTkFont(size=10), text_color=ACCENT_GREEN).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(h3, text="Posture", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(c3, text="Uptime", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack()

        # 1px Horizontal Separator Line (BORDER_SUBTLE)
        sep = ctk.CTkFrame(card_rings, fg_color=BORDER_SUBTLE, height=1)
        sep.pack(fill="x", padx=16, pady=(4, 6))

        # Session Analytics Section (2x2 Micro-Grid with live self. references)
        ctk.CTkLabel(card_rings, text="Session Analytics", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(0, 6))

        analytics_grid = ctk.CTkFrame(card_rings, fg_color="transparent")
        analytics_grid.pack(fill="x", padx=14, pady=(0, 10))
        analytics_grid.grid_columnconfigure((0, 1), weight=1)

        # Box 1: POSTURE UPTIME
        b1 = ctk.CTkFrame(analytics_grid, fg_color="#091829", border_color="#12334F", border_width=1, corner_radius=10)
        b1.grid(row=0, column=0, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(b1, text="POSTURE UPTIME", font=ctk.CTkFont(size=10, weight="bold"), text_color="#60A5FA").pack(anchor="center", pady=(5, 1))
        self.stat_posture_lbl = ctk.CTkLabel(b1, text="-- (Measuring)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED)
        self.stat_posture_lbl.pack(anchor="center", pady=(0, 5))

        # Box 2: AVG BLINK RATE
        b2 = ctk.CTkFrame(analytics_grid, fg_color="#071E17", border_color="#0F3F32", border_width=1, corner_radius=10)
        b2.grid(row=0, column=1, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(b2, text="AVG BLINK RATE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#34D399").pack(anchor="center", pady=(5, 1))
        self.stat_blink_lbl = ctk.CTkLabel(b2, text="-- (Measuring)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED)
        self.stat_blink_lbl.pack(anchor="center", pady=(0, 5))

        # Box 3: BREAKS COMPLETED (Dynamically linked to self._away_gazes_done)
        b3 = ctk.CTkFrame(analytics_grid, fg_color="#180C26", border_color="#361754", border_width=1, corner_radius=10)
        b3.grid(row=1, column=0, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(b3, text="BREAKS COMPLETED", font=ctk.CTkFont(size=10, weight="bold"), text_color="#C084FC").pack(anchor="center", pady=(5, 1))
        self.stat_breaks_lbl = ctk.CTkLabel(b3, text=f"{self._away_gazes_done} / 8 Cycles", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_PURPLE)
        self.stat_breaks_lbl.pack(anchor="center", pady=(0, 5))

        # Box 4: FATIGUE RISK
        b4 = ctk.CTkFrame(analytics_grid, fg_color="#071E17", border_color="#0F3F32", border_width=1, corner_radius=10)
        b4.grid(row=1, column=1, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(b4, text="FATIGUE RISK", font=ctk.CTkFont(size=10, weight="bold"), text_color="#34D399").pack(anchor="center", pady=(5, 1))
        self.stat_fatigue_lbl = ctk.CTkLabel(b4, text="-- (Measuring)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED)
        self.stat_fatigue_lbl.pack(anchor="center", pady=(0, 5))

        # ── 2. Bottom Telemetry Bar ───────────────────────────────────────────
        bottom_bar = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                  border_width=1, border_color=BORDER_CARD, height=48)
        bottom_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        bottom_bar.grid_propagate(False)

        # Left: "Session Telemetry" text
        ctk.CTkLabel(bottom_bar, text="Session Telemetry", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(side="left", padx=(18, 14), pady=12)

        # Glowing pill: [ Fatigue Relief Index: 92% ]
        self.relief_badge = ctk.CTkLabel(
            bottom_bar, text="Fatigue Relief Index: --", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#064E3B", text_color=TEXT_MUTED, corner_radius=12, padx=14, pady=4
        )
        self.relief_badge.pack(side="left", padx=4)

        # Right: Session: 45m (mapped to self._session_start)
        self.session_time_lbl = ctk.CTkLabel(bottom_bar, text="Session: 0m", font=ctk.CTkFont(size=12, weight="bold"),
                                             text_color=TEXT_PRIMARY)
        self.session_time_lbl.pack(side="right", padx=(0, 20))

        # Middle Right: Blink Rate: 18/min (mapped to self._current_bpm)
        self.blink_rate_lbl = ctk.CTkLabel(bottom_bar, text="Blink Rate: --", font=ctk.CTkFont(size=12),
                                           text_color=TEXT_PRIMARY)
        self.blink_rate_lbl.pack(side="right", padx=24)

        return page

    # ──────────────────────────────────────────────────────────────────────────
    #  Page 1: Cockpit (Preserved)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_page_cockpit(self):
        page = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0, minsize=370)
        page.grid_rowconfigure(0, weight=1)

        cam_col = ctk.CTkFrame(page, fg_color="transparent")
        cam_col.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        cam_col.grid_rowconfigure(0, weight=1)
        cam_col.grid_rowconfigure(1, weight=0)
        cam_col.grid_columnconfigure(0, weight=1)

        self.camera_frame = ctk.CTkFrame(cam_col, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                         border_width=1, border_color=BORDER_CARD)
        self.camera_frame.grid(row=0, column=0, sticky="nsew")
        self.camera_frame.grid_rowconfigure(0, weight=1)
        self.camera_frame.grid_columnconfigure(0, weight=1)

        self._placeholder = ctk.CTkFrame(self.camera_frame, fg_color="transparent")
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(self._placeholder, text="◈", font=ctk.CTkFont(size=54), text_color=ACCENT_CYAN).pack()
        ctk.CTkLabel(self._placeholder, text="Initializing Optical Engine...", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_SECONDARY).pack(pady=(6, 2))
        
        self.video_label = ctk.CTkLabel(self.camera_frame, text="", fg_color="transparent")

        # Corner HUD brackets
        ctk.CTkLabel(self.camera_frame, text="┌", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_CYAN).place(x=10, y=8)
        ctk.CTkLabel(self.camera_frame, text="┐", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_CYAN).place(relx=1.0, y=8, x=-20)

        # Quick Mode Pill Dock underneath camera
        dock_card = ctk.CTkFrame(cam_col, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                 border_width=1, border_color=BORDER_CARD, height=52)
        dock_card.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        dock_card.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        dock_card.grid_rowconfigure(0, weight=1)

        self.mode_pill_dock = {}
        for idx, mode in enumerate(["Left", "Right", "Double", "Drag", "Scroll", "Type"]):
            btn = ctk.CTkButton(
                dock_card, text=mode, font=ctk.CTkFont(size=11, weight="bold"),
                height=32, corner_radius=10, fg_color=BG_CARD_INNER, text_color=TEXT_SECONDARY,
                hover_color=BORDER_GLOW, command=lambda m=mode: self._set_quick_mode(m)
            )
            btn.grid(row=0, column=idx, padx=4, pady=6, sticky="ew")
            self.mode_pill_dock[mode] = btn
        self._update_quick_dock_styles()

        # Right Column Status Cards
        right_col = ctk.CTkFrame(page, fg_color="transparent", width=370)
        right_col.grid(row=0, column=1, sticky="nsew")
        right_col.grid_columnconfigure(0, weight=1)
        right_col.grid_propagate(False)

        ctk.CTkLabel(right_col, text="TELEMETRY RADAR", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED, anchor="w").grid(row=0, column=0, sticky="w", padx=4, pady=(0, 6))

        self.tracking_status_card = StatusCard(right_col, label="Head Tracking Engine", value="Paused")
        self.tracking_status_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.tracking_status_card.set_status("Paused", color=TEXT_MUTED)

        self.click_status_card = StatusCard(right_col, label="Actuation Engine", value="Ready to Dwell")
        self.click_status_card.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        # Ambient Light Intensity Guardian Card
        light_card = ctk.CTkFrame(right_col, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                  border_width=1, border_color=BORDER_CARD)
        light_card.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        light_card.grid_columnconfigure(0, weight=1)

        l_head = ctk.CTkFrame(light_card, fg_color="transparent")
        l_head.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(l_head, text="☀️ Ambient Light Guardian", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")
        self.lux_val_lbl = ctk.CTkLabel(l_head, text="Scene Brightness: --%", font=ctk.CTkFont(size=11, weight="bold"),
                                        text_color=ACCENT_GREEN)
        self.lux_val_lbl.pack(side="right")

        # Smooth Light Level Bar
        self.lux_bar = ctk.CTkProgressBar(light_card, height=6, fg_color=BG_PILL, progress_color=ACCENT_GREEN)
        self.lux_bar.set(0.55)
        self.lux_bar.pack(fill="x", padx=14, pady=(6, 4))

        self.lux_status_lbl = ctk.CTkLabel(
            light_card, text="🟢 Optimal Ergonomic Illumination", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=ACCENT_GREEN, anchor="w"
        )
        self.lux_status_lbl.pack(anchor="w", padx=14, pady=(0, 2))

        self.lux_tip_lbl = ctk.CTkLabel(
            light_card, text="Balanced room lighting minimizes eye fatigue and sensor noise.",
            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED, anchor="w"
        )
        self.lux_tip_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # Optical Tracking & Biometric Radar (3x2 Micro Grid)
        opt_card = ctk.CTkFrame(right_col, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=BORDER_CARD)
        opt_card.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        opt_card.grid_columnconfigure((0, 1), weight=1)

        # Row 0, Col 0: Face Mesh Lock
        mb1 = ctk.CTkFrame(opt_card, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        mb1.grid(row=0, column=0, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(mb1, text="FACE MESH LOCK", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(5, 1))
        self.cockpit_face_lbl = ctk.CTkLabel(mb1, text="Searching...", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        self.cockpit_face_lbl.pack(anchor="w", padx=8, pady=(0, 5))

        # Row 0, Col 1: Optical Speed & FPS
        mb2 = ctk.CTkFrame(opt_card, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        mb2.grid(row=0, column=1, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(mb2, text="ENGINE SPEED", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(5, 1))
        self.cockpit_speed_lbl = ctk.CTkLabel(mb2, text="-- FPS · --ms", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        self.cockpit_speed_lbl.pack(anchor="w", padx=8, pady=(0, 5))

        # Row 1, Col 0: Nose Reticle Tracking Lock
        mb_ret = ctk.CTkFrame(opt_card, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        mb_ret.grid(row=1, column=0, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(mb_ret, text="NOSE RETICLE", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(5, 1))
        self.cockpit_reticle_lbl = ctk.CTkLabel(mb_ret, text="Standby", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        self.cockpit_reticle_lbl.pack(anchor="w", padx=8, pady=(0, 5))

        # Row 1, Col 1: Mouth Emergency Brake State
        mb_mouth = ctk.CTkFrame(opt_card, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        mb_mouth.grid(row=1, column=1, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(mb_mouth, text="MOUTH BRAKE", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(5, 1))
        self.cockpit_mouth_lbl = ctk.CTkLabel(mb_mouth, text="Standby", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        self.cockpit_mouth_lbl.pack(anchor="w", padx=8, pady=(0, 5))

        # Row 2, Col 0: Eye Distance
        mb3 = ctk.CTkFrame(opt_card, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        mb3.grid(row=2, column=0, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(mb3, text="USER DISTANCE", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(5, 1))
        self.cockpit_dist_lbl = ctk.CTkLabel(mb3, text="No Face", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        self.cockpit_dist_lbl.pack(anchor="w", padx=8, pady=(0, 5))

        # Row 2, Col 1: Blink Frequency
        mb4 = ctk.CTkFrame(opt_card, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        mb4.grid(row=2, column=1, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(mb4, text="BLINK FREQUENCY", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(5, 1))
        self.cockpit_bpm_lbl = ctk.CTkLabel(mb4, text="-- BPM (Measuring)", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED)
        self.cockpit_bpm_lbl.pack(anchor="w", padx=8, pady=(0, 5))

        gym_cta = ctk.CTkButton(
            right_col, text="✦ View EyeRest Dashboard", font=ctk.CTkFont(size=12, weight="bold"),
            height=36, corner_radius=12, fg_color=ACCENT_CYAN, text_color=BG_MAIN,
            command=lambda: self._switch_tab("🫀 EyeRest")
        )
        gym_cta.grid(row=5, column=0, sticky="ew", pady=(2, 0))

        return page

    def _set_quick_mode(self, mode):
        self._click_mode.set(mode)
        self._update_quick_dock_styles()

    def _update_quick_dock_styles(self):
        curr = self._click_mode.get()
        for mode, btn in self.mode_pill_dock.items():
            if mode == curr:
                btn.configure(fg_color=ACCENT_CYAN, text_color=BG_MAIN)
            else:
                btn.configure(fg_color=BG_CARD_INNER, text_color=TEXT_SECONDARY)

    # ──────────────────────────────────────────────────────────────────────────
    #  Page 2: Motor / Navigation & Controls (Preserved)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_page_controls(self):
        page = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        page.grid_columnconfigure((0, 1), weight=1)
        self.motor_scroll_frame = page
        def _on_motor_scroll(event=None):
            self._last_scroll_time = time.monotonic()
        page.bind("<MouseWheel>", _on_motor_scroll, add="+")
        page.bind("<Button-4>", _on_motor_scroll, add="+")
        page.bind("<Button-5>", _on_motor_scroll, add="+")

        left_card = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                 border_width=1, border_color=BORDER_CARD)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=6)
        left_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_card, text="OPTICAL TRACKING CALIBRATION", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(16, 10))

        self.sensitivity_slider = LabeledSlider(left_card, title="Tracking Sensitivity Scale", from_=0.15, to=0.45, initial=self._sensitivity, command=self.on_sensitivity_change)
        self.sensitivity_slider.pack(fill="x", padx=16, pady=6)

        self.smoothing_slider = LabeledSlider(left_card, title="Cursor Speed / Alpha Smoothing", from_=0.1, to=1.0, initial=self._smoothing, command=self.on_smoothing_change)
        self.smoothing_slider.pack(fill="x", padx=16, pady=10)

        self.mouth_thresh_slider = LabeledSlider(left_card, title="Mouth Gesture Brake Threshold", from_=0.20, to=0.70, initial=self._mouth_thresh, command=self.on_mouth_thresh_change)
        self.mouth_thresh_slider.pack(fill="x", padx=16, pady=10)

        self.scroll_speed_slider = LabeledSlider(left_card, title="Smart Scroll Velocity", from_=100, to=1000, initial=self._scroll_speed, fmt=".0f", command=self.on_scroll_speed_change)
        self.scroll_speed_slider.pack(fill="x", padx=16, pady=(10, 18))

        right_card = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                  border_width=1, border_color=BORDER_CARD)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=6)
        right_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_card, text="ACTUATION MODES & FLOATING DOCK", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(16, 10))

        ctk.CTkLabel(right_card, text="Click Action Mode Selector", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(4, 6))

        self.click_mode_btn = ctk.CTkSegmentedButton(
            right_card, values=["Left", "Right", "Double", "Drag", "Scroll", "Type"], variable=self._click_mode,
            selected_color=ACCENT_CYAN, selected_hover_color=ACCENT_BLUE,
            unselected_color=BG_CARD_INNER, unselected_hover_color=BORDER_GLOW,
        )
        self.click_mode_btn.pack(fill="x", padx=16, pady=(0, 14))

        self.dock_pos_slider = LabeledSlider(right_card, title="Floating Dock Screen Position (X)", from_=0.0, to=1.0, initial=0.85, command=self.on_dock_move)
        self.dock_pos_slider.pack(fill="x", padx=16, pady=8)

        kb_box = ctk.CTkFrame(right_card, fg_color=BG_CARD_INNER, corner_radius=12)
        kb_box.pack(fill="x", padx=16, pady=(12, 16))
        
        ctk.CTkLabel(kb_box, text="Virtual Keyboard Hotkey", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(kb_box, text="Switch mode to 'Type' or dwell on input fields", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(0, 8))

        # ── ROW 1: Studio Bottom Extensions (Fills the empty space cleanly) ──
        # Bottom-Left Card: Dwell Calibration & Interactive Target Sandbox
        dwell_card = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                  border_width=1, border_color=BORDER_CARD)
        dwell_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 6))
        dwell_card.grid_columnconfigure(0, weight=1)

        dwell_head = ctk.CTkFrame(dwell_card, fg_color="transparent")
        dwell_head.pack(fill="x", padx=16, pady=(16, 6))
        ctk.CTkLabel(dwell_head, text="DWELL MATRIX & PRACTICE SANDBOX", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(dwell_head, text="Live Target Test", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=ACCENT_CYAN).pack(side="right")

        # Interactive Target Practice Canvas
        self.dwell_sandbox = DwellSandboxCanvas(dwell_card, height=135)
        self.dwell_sandbox.pack(fill="x", padx=16, pady=(0, 8))

        # Fine-tuning sliders for dwell timing and tremor deadzone
        self.dwell_time_slider = LabeledSlider(
            dwell_card, title="Dwell Hold Trigger Time", from_=0.4, to=2.0, initial=getattr(self, '_dwell_time', 1.0),
            fmt=".2f", command=self.on_dwell_time_change
        )
        self.dwell_time_slider.pack(fill="x", padx=16, pady=4)

        self.dwell_radius_slider = LabeledSlider(
            dwell_card, title="Tremor Deadzone / Jitter Radius", from_=15, to=50, initial=getattr(self, '_dwell_radius', 25),
            fmt=".0f", command=self.on_dwell_radius_change
        )
        self.dwell_radius_slider.pack(fill="x", padx=16, pady=(4, 16))

        # Bottom-Right Card: Smart Zone Scroll HUD & Kinematics Radar
        scroll_card = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                   border_width=1, border_color=BORDER_CARD)
        scroll_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 6))
        scroll_card.grid_columnconfigure(0, weight=1)

        scroll_head = ctk.CTkFrame(scroll_card, fg_color="transparent")
        scroll_head.pack(fill="x", padx=16, pady=(16, 6))
        ctk.CTkLabel(scroll_head, text="SMART ZONE SCROLL & KINEMATICS RADAR", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(scroll_head, text="Real-Time Altitude", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=ACCENT_CYAN).pack(side="right")

        # Visual Scroll Zone Radar Diagram
        self.scroll_radar = ScrollRadarCanvas(scroll_card, height=135)
        self.scroll_radar.pack(fill="x", padx=16, pady=(0, 8))

        # 2x2 Diagnostics Micro-Tiles
        diag_grid = ctk.CTkFrame(scroll_card, fg_color="transparent")
        diag_grid.pack(fill="x", padx=14, pady=(0, 16))
        diag_grid.grid_columnconfigure((0, 1), weight=1)

        # Tile 1: Projected Coordinates
        t1 = ctk.CTkFrame(diag_grid, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        t1.grid(row=0, column=0, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(t1, text="CURSOR PROJECTION", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(6, 1))
        self.motor_coords_lbl = ctk.CTkLabel(t1, text="X: -- | Y: --", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_CYAN)
        self.motor_coords_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        # Tile 2: Tremor Stability Filter
        t2 = ctk.CTkFrame(diag_grid, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        t2.grid(row=0, column=1, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(t2, text="TREMOR DAMPENING", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(6, 1))
        self.motor_stab_lbl = ctk.CTkLabel(t2, text="98.5% (Stable)", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_GREEN)
        self.motor_stab_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        # Tile 3: Actuation Mechanism
        t3 = ctk.CTkFrame(diag_grid, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        t3.grid(row=1, column=0, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(t3, text="ACTUATION MECHANISM", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(6, 1))
        self.motor_act_lbl = ctk.CTkLabel(t3, text=f"Dwell Timer ({getattr(self, '_dwell_time', 1.0):.1f}s)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY)
        self.motor_act_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        # Tile 4: Scroll State
        t4 = ctk.CTkFrame(diag_grid, fg_color=BG_CARD_INNER, corner_radius=10, border_width=1, border_color=BORDER_CARD)
        t4.grid(row=1, column=1, padx=4, pady=3, sticky="nsew")
        ctk.CTkLabel(t4, text="SCROLL THRESHOLD", font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(6, 1))
        self.motor_scroll_state_lbl = ctk.CTkLabel(t4, text="35% / 65% Bounds", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_BLUE)
        self.motor_scroll_state_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        # ── ROW 2: Bottom Ergonomic Calibration Action Toolbar ────────────────
        tools_card = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                  border_width=1, border_color=BORDER_CARD, height=48)
        tools_card.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 14))
        tools_card.grid_columnconfigure((0, 1, 2), weight=1)

        btn_recenter = ctk.CTkButton(
            tools_card, text="🎯  Zero-Point Neutral Calibration", font=ctk.CTkFont(size=11, weight="bold"),
            height=34, corner_radius=10, fg_color=BG_CARD_INNER, hover_color=BORDER_GLOW,
            text_color=TEXT_PRIMARY, command=self._action_recenter
        )
        btn_recenter.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        btn_practice_reset = ctk.CTkButton(
            tools_card, text="↺  Reset Sandbox Hits", font=ctk.CTkFont(size=11, weight="bold"),
            height=34, corner_radius=10, fg_color=BG_CARD_INNER, hover_color=BORDER_GLOW,
            text_color=TEXT_SECONDARY, command=self._action_reset_sandbox
        )
        btn_practice_reset.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        btn_reset_defaults = ctk.CTkButton(
            tools_card, text="⚙  Restore Motor Defaults", font=ctk.CTkFont(size=11, weight="bold"),
            height=34, corner_radius=10, fg_color=BG_CARD_INNER, hover_color=BORDER_GLOW,
            text_color=ACCENT_CYAN, command=self._action_restore_defaults
        )
        btn_reset_defaults.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        return page

    def on_dwell_time_change(self, v):
        self._dwell_time = float(v)
        if hasattr(self, 'dwell_sandbox'):
            self.dwell_sandbox.set_params(self._dwell_time, getattr(self, '_dwell_radius', 25))
        if hasattr(self, 'motor_act_lbl'):
            self.motor_act_lbl.configure(text=f"Dwell Timer ({self._dwell_time:.2f}s)")
        self._mark_custom()
        self._save_profile()

    def on_dwell_radius_change(self, v):
        self._dwell_radius = int(float(v))
        if hasattr(self, 'dwell_sandbox'):
            self.dwell_sandbox.set_params(getattr(self, '_dwell_time', 1.0), self._dwell_radius)
        self._mark_custom()
        self._save_profile()

    def _action_recenter(self):
        if getattr(self, '_face_present', False):
            self._neutral_x = float(getattr(self, '_raw_nose_x', 0.5))
            self._neutral_y = float(getattr(self, '_raw_nose_y', 0.5))
            self._ts_status(f"🎯 Zero-Point Calibrated to ({self._neutral_x:.2f}, {self._neutral_y:.2f})!", color=ACCENT_GREEN)
            self._ts_flash(color=ACCENT_GREEN)
        else:
            self._neutral_x = 0.5
            self._neutral_y = 0.5
            self._ts_status("Reset Origin to Center (0.50, 0.50)", color=ACCENT_CYAN)
            self._ts_flash(color=ACCENT_CYAN)

    def _action_reset_sandbox(self):
        if hasattr(self, 'dwell_sandbox'):
            self.dwell_sandbox.reset_hits()

    def _action_restore_defaults(self):
        self._sensitivity = 0.25
        self._smoothing = 0.50
        self._mouth_thresh = 0.40
        self._scroll_speed = 360
        self._dwell_time = 1.0
        self._dwell_radius = 25
        if hasattr(self, 'sensitivity_slider'):
            self.sensitivity_slider.set_value(self._sensitivity)
        if hasattr(self, 'smoothing_slider'):
            self.smoothing_slider.set_value(self._smoothing)
        if hasattr(self, 'mouth_thresh_slider'):
            self.mouth_thresh_slider.set_value(self._mouth_thresh)
        if hasattr(self, 'scroll_speed_slider'):
            self.scroll_speed_slider.set_value(self._scroll_speed)
        if hasattr(self, 'dwell_time_slider'):
            self.dwell_time_slider.set_value(self._dwell_time)
        if hasattr(self, 'dwell_radius_slider'):
            self.dwell_radius_slider.set_value(self._dwell_radius)
        if hasattr(self, 'dwell_sandbox'):
            self.dwell_sandbox.set_params(self._dwell_time, self._dwell_radius)
        if hasattr(self, 'motor_act_lbl'):
            self.motor_act_lbl.configure(text="Dwell Timer (1.0s)")
        self._active_preset = "Default"
        self._save_profile()
        self._refresh_profile_widgets()
        self._ts_status("Defaults Restored!", color=ACCENT_CYAN)

    # ──────────────────────────────────────────────────────────────────────────
    #  Page 4: Dedicated Figure-8 Eye Gym Tab (Upgraded Layout & XP Rewards)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_page_gym(self):
        page = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=0, minsize=410)
        page.grid_rowconfigure(0, weight=1)

        # ── Left Column: High-Fidelity Workout Arena & Interactive Controls ───
        left_box = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                border_width=1, border_color=BORDER_CARD)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_box.grid_columnconfigure(0, weight=1)
        left_box.grid_rowconfigure(1, weight=1)
        left_box.grid_rowconfigure(2, weight=0)

        # Header row
        header_row = ctk.CTkFrame(left_box, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))
        ctk.CTkLabel(header_row, text="GAMIFIED FIGURE-8 EYE GYMNASTICS",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
        self.gym_mode_badge = ctk.CTkLabel(header_row, text="● Active Routine: Infinity Flow",
                                           font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_CYAN)
        self.gym_mode_badge.pack(side="right")

        # Upgraded Luminous Glowing Canvas (Exact Image 2 Replica)
        self.dedicated_gym_canvas = Figure8GymCanvas(left_box, width=540, height=270, on_lap=self._on_gym_lap_done, master_app=self)
        self.dedicated_gym_canvas.grid(row=1, column=0, padx=16, pady=(2, 8), sticky="nsew")

        # Lower Workout Deck (Unified Full-Width Card to prevent any text clipping)
        deck = ctk.CTkFrame(left_box, fg_color=BG_CARD_INNER, corner_radius=12,
                            border_width=1, border_color=BORDER_SUBTLE)
        deck.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        deck.grid_columnconfigure(0, weight=1)

        # ── Row 1: Exercise Routine Selector & Session Controls ──────────────
        routine_bar = ctk.CTkFrame(deck, fg_color="transparent")
        routine_bar.pack(fill="x", padx=12, pady=(10, 6))

        # Routine Selector Buttons (prominent, full visibility, cannot be clipped):
        self.btn_pat_fig8 = ctk.CTkButton(
            routine_bar, text="♾  Figure-8 Lemniscate", font=ctk.CTkFont(size=11, weight="bold"),
            height=32, corner_radius=8, fg_color=BG_PILL_ACTIVE, text_color=ACCENT_CYAN,
            hover_color=BORDER_GLOW, command=lambda: self._action_set_gym_pattern("figure8")
        )
        self.btn_pat_fig8.pack(side="left", padx=(0, 6), expand=True, fill="x")

        self.btn_pat_horiz = ctk.CTkButton(
            routine_bar, text="⟷  Smooth Pursuit (Horizontal)", font=ctk.CTkFont(size=11, weight="bold"),
            height=32, corner_radius=8, fg_color=BG_CARD, text_color=TEXT_SECONDARY,
            hover_color=BORDER_GLOW, command=lambda: self._action_set_gym_pattern("horizontal")
        )
        self.btn_pat_horiz.pack(side="left", padx=(0, 10), expand=True, fill="x")

        # Session controls:
        self.btn_gym_play = ctk.CTkButton(
            routine_bar, text="⏸  Pause", font=ctk.CTkFont(size=11, weight="bold"),
            width=76, height=32, corner_radius=8, fg_color=BG_SURFACE, hover_color=BORDER_GLOW,
            text_color=TEXT_PRIMARY, command=self._action_toggle_gym
        )
        self.btn_gym_play.pack(side="left", padx=(0, 4))

        btn_gym_reset = ctk.CTkButton(
            routine_bar, text="↺  Reset", font=ctk.CTkFont(size=11, weight="bold"),
            width=68, height=32, corner_radius=8, fg_color=BG_CARD, hover_color=BORDER_GLOW,
            text_color=TEXT_SECONDARY, command=self._action_reset_gym
        )
        btn_gym_reset.pack(side="left")

        # ── Row 2: Cadence Pacing Pills & Progress ────────────────────────────
        pacing_bar = ctk.CTkFrame(deck, fg_color="transparent")
        pacing_bar.pack(fill="x", padx=12, pady=(0, 6))

        # Pack progress label to the right FIRST so it is always fully visible and never clipped:
        self.gym_lap_progress_lbl = ctk.CTkLabel(
            pacing_bar, text="Progress: 0 / 10 Laps (+50 XP)",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_CYAN
        )
        self.gym_lap_progress_lbl.pack(side="right", padx=(6, 0))

        ctk.CTkLabel(pacing_bar, text="Cadence:", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 6))

        self.btn_speed_07 = ctk.CTkButton(
            pacing_bar, text="🧘 Relaxed (14s)", font=ctk.CTkFont(size=10), height=26, corner_radius=6,
            fg_color=BG_CARD, hover_color=BORDER_GLOW, text_color=TEXT_SECONDARY,
            command=lambda: self._action_set_gym_speed(11.0 / 14.0)
        )
        self.btn_speed_07.pack(side="left", padx=2)

        self.btn_speed_10 = ctk.CTkButton(
            pacing_bar, text="🟢 Normal (11s)", font=ctk.CTkFont(size=10, weight="bold"), height=26, corner_radius=6,
            fg_color=BG_PILL_ACTIVE, hover_color=BORDER_GLOW, text_color=ACCENT_CYAN,
            command=lambda: self._action_set_gym_speed(1.0)
        )
        self.btn_speed_10.pack(side="left", padx=2)

        self.btn_speed_14 = ctk.CTkButton(
            pacing_bar, text="⚡ Agile (8s · Lvl 3)", font=ctk.CTkFont(size=10), height=26, corner_radius=6,
            fg_color=BG_CARD, hover_color=BORDER_GLOW, text_color=TEXT_MUTED,
            command=lambda: self._action_set_gym_speed(11.0 / 8.0)
        )
        self.btn_speed_14.pack(side="left", padx=2)

        self.gym_lap_bar = ctk.CTkProgressBar(deck, height=6, corner_radius=3, fg_color="#0A1324",
                                              progress_color=ACCENT_CYAN)
        self.gym_lap_bar.pack(fill="x", padx=12, pady=(0, 6))
        self.gym_lap_bar.set(0.0)

        # Reassurance tip:
        ctk.CTkLabel(
            deck, text="🧘 Neck Comfort Active: Keep head in neutral posture. Follow orb with eyes to release cervical & ocular tension.",
            font=ctk.CTkFont(size=10), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # ── Right Column: XP Progression, Perk Unlocks & Ocular Telemetry ─────
        right_box = ctk.CTkFrame(page, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                                 border_width=1, border_color=BORDER_CARD)
        right_box.grid(row=0, column=1, sticky="nsew")
        right_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_box, text="PROGRESSION & XP REWARDS HUB", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(10, 6))

        # 1. Level & Next Perk Unlock Card
        lvl_box = ctk.CTkFrame(right_box, fg_color=BG_CARD_INNER, corner_radius=12,
                               border_width=1, border_color=BORDER_SUBTLE)
        lvl_box.pack(fill="x", padx=16, pady=(0, 6))

        top_lvl = ctk.CTkFrame(lvl_box, fg_color="transparent")
        top_lvl.pack(fill="x", padx=14, pady=(8, 2))

        self.gym_level_lbl = ctk.CTkLabel(top_lvl, text=f"LEVEL {self._player_level} · {self._rank_title().upper()}",
                                          font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_PURPLE)
        self.gym_level_lbl.pack(side="left")

        self.gym_xp_total_lbl = ctk.CTkLabel(top_lvl, text=f"{self._player_xp} XP",
                                            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_GOLD)
        self.gym_xp_total_lbl.pack(side="right")

        self.gym_rank_lbl = ctk.CTkLabel(lvl_box, text=self._rank_line(), font=ctk.CTkFont(size=10), text_color=TEXT_SECONDARY)
        self.gym_rank_lbl.pack(anchor="w", padx=14, pady=(0, 4))

        self.gym_xp_bar = ctk.CTkProgressBar(lvl_box, height=7, corner_radius=3, fg_color="#0A1324",
                                             progress_color=ACCENT_PURPLE)
        self.gym_xp_bar.pack(fill="x", padx=14, pady=(0, 4))
        self.gym_xp_bar.set(min(1.0, (self._player_xp % self.XP_PER_LEVEL) / self.XP_PER_LEVEL))

        # Next Unlock Milestone Banner
        self.gym_next_unlock_lbl = ctk.CTkLabel(
            lvl_box, text="🎁 Next Unlock (Level 2 · 500 XP): Emerald Theme & Focus Multiplier",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_CYAN, wraplength=370, justify="left"
        )
        self.gym_next_unlock_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        # 2. 2x2 Ocular Fitness Telemetry Grid
        grid_frame = ctk.CTkFrame(right_box, fg_color="transparent")
        grid_frame.pack(fill="x", padx=16, pady=(0, 6))
        grid_frame.grid_columnconfigure((0, 1), weight=1)

        def make_gym_tile(row, col, title, initial_val, colr=TEXT_PRIMARY):
            f = ctk.CTkFrame(grid_frame, fg_color=BG_CARD_INNER, corner_radius=10,
                             border_width=1, border_color=BORDER_SUBTLE)
            f.grid(row=row, column=col, sticky="nsew", padx=3, pady=2)
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(6, 1))
            lbl = ctk.CTkLabel(f, text=initial_val, font=ctk.CTkFont(size=11, weight="bold"),
                              text_color=colr)
            lbl.pack(anchor="w", padx=8, pady=(0, 6))
            return lbl

        self.gym_sync_lbl = make_gym_tile(0, 0, "GAZE LOCK SYNC", "98.0% (Optimal)", ACCENT_GREEN)
        self.gym_laps_lbl = make_gym_tile(0, 1, "SESSION LAPS", "0 / 10 Laps", ACCENT_CYAN)
        self.gym_xp_session_lbl = make_gym_tile(1, 0, "XP THIS SESSION", "+0 XP", ACCENT_PURPLE)
        self.gym_streak_lbl = make_gym_tile(1, 1, "STREAK BOOST", f"🔥 {self._streak()}d (1.5x Mult)", ACCENT_AMBER)

        # 3. Progression Tree & Unlockable Perks Showcase
        ctk.CTkLabel(right_box, text="OCULAR PERKS & MILESTONE UNLOCKS", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(2, 4))

        self.perk_cards_frame = ctk.CTkFrame(right_box, fg_color="transparent")
        self.perk_cards_frame.pack(fill="x", padx=16, pady=(0, 6))

        def make_perk_tile(title, status_txt, is_unlocked, desc, on_click=None):
            c = ctk.CTkFrame(self.perk_cards_frame, fg_color=BG_CARD_INNER, corner_radius=10,
                             border_width=1, border_color=BORDER_GLOW if is_unlocked else BORDER_SUBTLE,
                             cursor="hand2" if on_click else "")
            c.pack(fill="x", pady=2)
            h = ctk.CTkFrame(c, fg_color="transparent")
            h.pack(fill="x", padx=10, pady=(5, 1))
            t_lbl = ctk.CTkLabel(h, text=title, font=ctk.CTkFont(size=10, weight="bold"),
                                 text_color=TEXT_PRIMARY if is_unlocked else TEXT_SECONDARY)
            t_lbl.pack(side="left")
            s_col = ACCENT_GREEN if "ACTIVE" in status_txt else (ACCENT_CYAN if is_unlocked else TEXT_MUTED)
            s_lbl = ctk.CTkLabel(h, text=status_txt, font=ctk.CTkFont(size=10, weight="bold"), text_color=s_col)
            s_lbl.pack(side="right")
            d_lbl = ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=10), text_color=TEXT_MUTED,
                                 wraplength=370, justify="left")
            d_lbl.pack(anchor="w", padx=10, pady=(0, 5))
            if on_click:
                for widget in (c, h, t_lbl, s_lbl, d_lbl):
                    widget.bind("<Button-1>", lambda e, fn=on_click: fn())
            return c, s_lbl

        lvl = self._player_level
        self.perk_t1_card, self.perk_t1_stat = make_perk_tile(
            "♾ Lemniscate Flow (Level 1)", "✓ ACTIVE", True,
            "Full orbital 360° lemniscate pursuit stimulates oblique & rectus ocular muscles.",
            on_click=lambda: self._action_set_gym_pattern("figure8")
        )
        self.perk_t2_card, self.perk_t2_stat = make_perk_tile(
            "⟷ Smooth Pursuit Saccades",
            "▶ SELECT ROUTINE", True,
            "Horizontal saccadic eye sweeping relieves fixed-focus screen stare and dry-eye spasm. Click to switch!",
            on_click=lambda: self._action_set_gym_pattern("horizontal")
        )
        self.perk_t3_card, self.perk_t3_stat = make_perk_tile(
            "⚡ Agile 1.4x Cadence & Gold Reticle (Level 3 · 1,000 XP)",
            "✓ UNLOCKED" if lvl >= 3 else "🔒 LOCKED (1,000 XP)", lvl >= 3,
            "High-cadence optical agility tracking with luminous high-contrast gold reticle skin."
        )

        # 4. Quick Action Guided Routine CTA
        self.btn_guided_routine = ctk.CTkButton(
            right_box, text="⚡  Start Guided 2-Min Eye Routine (+100 XP)",
            font=ctk.CTkFont(size=11, weight="bold"), height=34, corner_radius=10,
            fg_color=BG_SURFACE, hover_color=BORDER_GLOW, text_color=ACCENT_CYAN,
            command=self._action_start_guided_routine
        )
        self.btn_guided_routine.pack(fill="x", padx=16, pady=(2, 8))

        return page

    # ── EyeGym Actions & XP Utility Handlers ──────────────────────────────────
    def _award_xp(self, amount: int, reason: str = None, save: bool = True):
        """Awards XP, applies unlocked streak (1.5x) or Vision Master (2x) perks, triggers level-up, and persists profile."""
        mult = 1.0
        mult_tag = ""
        if self._player_level >= 8:
            mult = 2.0
            mult_tag = " (2x Master Boost)"
        elif self._streak() >= 3:
            mult = 1.5
            mult_tag = " (1.5x Streak Boost)"

        final_amount = int(round(amount * mult))
        self._player_xp += final_amount
        self._session_gym_xp = getattr(self, '_session_gym_xp', 0) + final_amount
        new_lvl = self._level_for_xp(self._player_xp)
        leveled_up = (new_lvl > self._player_level)
        if leveled_up:
            self._player_level = new_lvl
            self._ts_status(f"🎉 LEVEL UP! You reached Level {new_lvl} ({self._rank_title()})!", color=ACCENT_GOLD)
            self._ts_flash(color=ACCENT_GOLD)
        elif reason:
            self._ts_status(f"+{final_amount} XP: {reason}{mult_tag}!", color=ACCENT_PURPLE)
            self._ts_flash(color=ACCENT_PURPLE)

        if save or leveled_up:
            self._save_profile()
        self._refresh_profile_widgets()
        self._refresh_gym_widgets()

    def _on_gym_lap_done(self, lap_count: int, earned_xp: int = 50, accuracy: float = 95.0):
        """Called when a lap is completed by user tracing along the neon track."""
        if not getattr(self, '_face_present', False):
            return
        
        is_milestone = (lap_count % 10 == 0)
        self._award_xp(earned_xp, reason=f"Lap {lap_count} Traced ({accuracy:.0f}% Acc)", save=True)
        if is_milestone:
            self._award_xp(50, reason="10-Lap Milestone Bonus", save=True)
            self._ts_status("🏅 10 Laps Complete! +50 XP Bonus Awarded!", color=ACCENT_GREEN)
            self._ts_flash(color=ACCENT_GREEN)
        else:
            self._ts_status(f"🎯 Lap {lap_count} Traced! {accuracy:.0f}% Accuracy (+{earned_xp} XP)", color=ACCENT_GREEN if accuracy >= 80 else ACCENT_CYAN)
            self._ts_flash(color=ACCENT_GREEN if accuracy >= 80 else ACCENT_CYAN)
        self._refresh_gym_widgets()

    def _action_toggle_gym(self):
        if hasattr(self, 'dedicated_gym_canvas'):
            is_running = self.dedicated_gym_canvas.toggle_play()
            txt = "⏸  Pause Workout" if is_running else "▶  Resume Workout"
            if hasattr(self, 'btn_gym_play'):
                self.btn_gym_play.configure(text=txt)
            if hasattr(self, 'gym_mode_badge'):
                stat = "● Active Routine: Running" if is_running else "⏸ Workout Paused"
                col = ACCENT_CYAN if is_running else TEXT_MUTED
                self.gym_mode_badge.configure(text=stat, text_color=col)

    def _action_reset_gym(self):
        if hasattr(self, 'dedicated_gym_canvas'):
            self.dedicated_gym_canvas.reset_laps()
            self._refresh_gym_widgets()
            self._ts_status("EyeGym Laps Reset!", color=ACCENT_CYAN)

    def _action_set_gym_speed(self, speed_val: float):
        if speed_val >= 1.2 and self._player_level < 3:
            self._ts_status("🔒 Agile 8s unlocks at Level 3 (1,000 XP)! Complete laps to level up.", color=ACCENT_AMBER)
            self._ts_flash(color=ACCENT_AMBER)
            return
        if hasattr(self, 'dedicated_gym_canvas'):
            self.dedicated_gym_canvas.set_speed(speed_val)
        if hasattr(self, 'btn_speed_07'):
            is_relaxed = abs(speed_val - (11.0 / 14.0)) < 0.05
            is_normal = abs(speed_val - 1.0) < 0.05
            is_agile = abs(speed_val - (11.0 / 8.0)) < 0.05
            self.btn_speed_07.configure(fg_color=BG_PILL_ACTIVE if is_relaxed else BG_CARD,
                                        text_color=ACCENT_CYAN if is_relaxed else TEXT_SECONDARY)
            self.btn_speed_10.configure(fg_color=BG_PILL_ACTIVE if is_normal else BG_CARD,
                                        text_color=ACCENT_CYAN if is_normal else TEXT_SECONDARY)
            self.btn_speed_14.configure(fg_color=BG_PILL_ACTIVE if is_agile else BG_CARD,
                                        text_color=ACCENT_CYAN if is_agile else TEXT_MUTED)

    def _action_set_gym_pattern(self, pat_name: str):
        if hasattr(self, 'dedicated_gym_canvas'):
            self.dedicated_gym_canvas.set_pattern(pat_name)
        is_fig8 = (pat_name == "figure8")
        if hasattr(self, 'btn_pat_fig8'):
            self.btn_pat_fig8.configure(fg_color=BG_PILL_ACTIVE if is_fig8 else BG_CARD,
                                        text_color=ACCENT_CYAN if is_fig8 else TEXT_SECONDARY)
        if hasattr(self, 'btn_pat_horiz'):
            self.btn_pat_horiz.configure(fg_color=BG_PILL_ACTIVE if not is_fig8 else BG_CARD,
                                         text_color=ACCENT_CYAN if not is_fig8 else TEXT_SECONDARY)
        if hasattr(self, 'perk_t1_stat'):
            self.perk_t1_stat.configure(text="✓ ACTIVE" if is_fig8 else "▶ SELECT",
                                        text_color=ACCENT_GREEN if is_fig8 else ACCENT_CYAN)
        if hasattr(self, 'perk_t2_stat'):
            self.perk_t2_stat.configure(text="✓ ACTIVE" if not is_fig8 else "▶ SELECT",
                                        text_color=ACCENT_GREEN if not is_fig8 else ACCENT_CYAN)
        if hasattr(self, 'perk_t1_card'):
            self.perk_t1_card.configure(border_color=BORDER_GLOW if is_fig8 else BORDER_SUBTLE)
        if hasattr(self, 'perk_t2_card'):
            self.perk_t2_card.configure(border_color=BORDER_GLOW if not is_fig8 else BORDER_SUBTLE)
        if hasattr(self, 'gym_mode_badge'):
            p_txt = "● Active Routine: Figure-8 Lemniscate" if is_fig8 else "● Active Routine: Smooth Pursuit (Horizontal)"
            self.gym_mode_badge.configure(text=p_txt, text_color=ACCENT_CYAN)
        self._ts_status(f"Routine Switched: {'Figure-8 Lemniscate' if is_fig8 else 'Smooth Pursuit Horizontal'}!", color=ACCENT_CYAN)
        self._ts_flash(color=ACCENT_CYAN)

    def _action_start_guided_routine(self):
        """Starts a 2-minute timed ocular relaxation routine with +100 XP reward."""
        if hasattr(self, '_routine_running') and self._routine_running:
            self._ts_status("Guided Routine already in progress!", color=ACCENT_AMBER)
            return
        self._routine_running = True
        self._routine_secs_left = 120
        self._routine_tracked_secs = 0
        self._ts_status("⚡ Starting 2-Min Guided Eye Routine! Focus on the moving orb.", color=ACCENT_CYAN)
        self._ts_flash(color=ACCENT_CYAN)

        if hasattr(self, 'dedicated_gym_canvas'):
            self.dedicated_gym_canvas.is_running = True
            if hasattr(self, 'btn_gym_play'):
                self.btn_gym_play.configure(text="⏸  Pause Workout")

        def _tick_routine():
            if not getattr(self, '_routine_running', False):
                return
            self._routine_secs_left -= 1

            # XP Farming Fix: Only count engagement when face is present and user is tracking
            is_tracking = getattr(self, '_face_present', False) and (
                hasattr(self, 'dedicated_gym_canvas') and self.dedicated_gym_canvas.locked
            )
            if is_tracking:
                self._routine_tracked_secs += 1

            if hasattr(self, 'btn_guided_routine'):
                m, s = divmod(self._routine_secs_left, 60)
                tracked_pct = int((self._routine_tracked_secs / max(1, 120 - self._routine_secs_left)) * 100)
                self.btn_guided_routine.configure(text=f"⏱  Routine: {m:02d}:{s:02d} left ({tracked_pct}% locked)")
            if self._routine_secs_left <= 0:
                self._routine_running = False
                if hasattr(self, 'btn_guided_routine'):
                    self.btn_guided_routine.configure(text="⚡  Start Guided 2-Min Eye Routine (+100 XP)")
                # Item 12: Require real focus time (at least 60s active lock-on) for the +100 XP routine
                if self._routine_tracked_secs >= 60:
                    self._award_xp(100, reason="2-Min Routine Completed", save=True)
                    self._ts_status("🎉 Routine Complete! Focused ocular tracking verified. +100 XP Awarded!", color=ACCENT_GREEN)
                    self._ts_flash(color=ACCENT_GREEN)
                else:
                    self._ts_status(f"⚠️ Routine Ended: {self._routine_tracked_secs}s locked (<60s required). Continuous focus required for +100 XP.", color=ACCENT_AMBER)
                    self._ts_flash(color=ACCENT_AMBER)
            else:
                self.after(1000, _tick_routine)

        self.after(1000, _tick_routine)

    def _refresh_gym_widgets(self):
        """Pushes current level, XP progress, perks, and telemetry into EyeGym widgets."""
        if not hasattr(self, 'gym_level_lbl'):
            return
        lvl = self._player_level
        rank = self._rank_title()
        self._set_label(self.gym_level_lbl, f"LEVEL {lvl} · {rank.upper()}")
        if hasattr(self, 'gym_xp_total_lbl'):
            self._set_label(self.gym_xp_total_lbl, f"{self._player_xp} XP")
        self._set_label(self.gym_rank_lbl, self._rank_line())

        in_lvl = self._player_xp % self.XP_PER_LEVEL
        if hasattr(self, 'gym_xp_bar'):
            self.gym_xp_bar.set(min(1.0, in_lvl / float(self.XP_PER_LEVEL)))

        # Next perk unlock text matching exact mathematical code thresholds:
        if hasattr(self, 'gym_next_unlock_lbl'):
            if lvl == 1:
                next_txt = "🎁 Next Unlock (Level 2 · 500 XP): Emerald Theme & Focus Multiplier"
            elif lvl == 2:
                next_txt = "🎁 Next Unlock (Level 3 · 1,000 XP): Agile 8s Cadence Pace + Gold Reticle Skin"
            elif lvl == 3:
                next_txt = "🎁 Next Unlock (Level 4 · 1,500 XP): Zen Breath Synchronizer Mode (4s Paced Cadence)"
            elif lvl < 8:
                xp_for_master = (8 - 1) * self.XP_PER_LEVEL
                next_txt = f"🎁 Next Unlock (Level 8 · {xp_for_master:,} XP): Vision Master Max Rank + Permanent 2x XP Multiplier"
            else:
                next_txt = "👑 Max Rank Reached: Vision Master! Permanent 2x XP Multiplier Active!"
            self._set_label(self.gym_next_unlock_lbl, next_txt)

        # Dynamic streak pill text and perk multiplier feedback:
        if hasattr(self, 'gym_streak_lbl'):
            stk = self._streak()
            if lvl >= 8:
                stk_txt = "👑 Max (2.0x XP Mult)"
            elif stk >= 3:
                stk_txt = f"🔥 {stk}d (1.5x Mult Active)"
            else:
                stk_txt = f"🔥 {stk}d ({3 - stk}d to 1.5x Mult)"
            self._set_label(self.gym_streak_lbl, stk_txt, ACCENT_AMBER)

        # Telemetry updates
        if hasattr(self, 'dedicated_gym_canvas'):
            laps = self.dedicated_gym_canvas.laps_done
            acc = self.dedicated_gym_canvas.accuracy
            locked = self.dedicated_gym_canvas.locked
            if hasattr(self, 'gym_laps_lbl'):
                self._set_label(self.gym_laps_lbl, f"{laps} / 10 Laps")
            if hasattr(self, 'gym_sync_lbl'):
                stat_txt = f"{acc:.1f}% (Locked)" if locked else f"{acc:.1f}% (Tracking)"
                stat_col = ACCENT_GREEN if locked else ACCENT_AMBER
                self._set_label(self.gym_sync_lbl, stat_txt, stat_col)
            if hasattr(self, 'gym_lap_progress_lbl'):
                self._set_label(self.gym_lap_progress_lbl, f"Progress: {laps % 10} / 10 Laps (+50 XP)")
            if hasattr(self, 'gym_lap_bar'):
                self.gym_lap_bar.set(min(1.0, (laps % 10) / 10.0))

        if hasattr(self, 'gym_xp_session_lbl'):
            s_xp = getattr(self, '_session_gym_xp', 0)
            self._set_label(self.gym_xp_session_lbl, f"+{s_xp} XP")

        # Perk tile unlock state
        is_fig8 = getattr(self.dedicated_gym_canvas, 'pattern', 'figure8') == 'figure8' if hasattr(self, 'dedicated_gym_canvas') else True
        if hasattr(self, 'perk_t1_stat'):
            self._set_label(self.perk_t1_stat, "✓ ACTIVE" if is_fig8 else "▶ SELECT", ACCENT_GREEN if is_fig8 else ACCENT_CYAN)
        if hasattr(self, 'perk_t2_stat'):
            self._set_label(self.perk_t2_stat, "✓ ACTIVE" if not is_fig8 else "▶ SELECT", ACCENT_GREEN if not is_fig8 else ACCENT_CYAN)
        if hasattr(self, 'perk_t3_stat'):
            self._set_label(self.perk_t3_stat, "✓ UNLOCKED" if lvl >= 3 else "🔒 LOCKED (1,000 XP)",
                            ACCENT_GREEN if lvl >= 3 else TEXT_MUTED)

    # ──────────────────────────────────────────────────────────────────────────
    #  Page 5: User Profile & Presets (Preserved)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_page_profile(self):
        page = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=11)
        page.grid_columnconfigure(1, weight=9)
        self.profile_scroll_frame = page
        def _on_profile_scroll(event=None):
            self._last_scroll_time = time.monotonic()
        page.bind("<MouseWheel>", _on_profile_scroll, add="+")
        page.bind("<Button-4>", _on_profile_scroll, add="+")
        page.bind("<Button-5>", _on_profile_scroll, add="+")

        left_col = ctk.CTkFrame(page, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="new", padx=(0, 10))
        right_col = ctk.CTkFrame(page, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="new", padx=(10, 0))

        def card(parent):
            c = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=CORNER_RADIUS,
                             border_width=1, border_color=BORDER_CARD)
            c.pack(fill="x", pady=(0, 14))
            return c

        # ── Hero: avatar, name, rank, device, weekly streak ──────────────────
        hero = card(left_col)
        top = ctk.CTkFrame(hero, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(18, 10))

        self.pf_avatar = ctk.CTkLabel(top, text=self._initials(), font=ctk.CTkFont(size=26, weight="bold"),
                                      fg_color=ACCENT_PURPLE, text_color=TEXT_PRIMARY,
                                      width=76, height=76, corner_radius=38)
        self.pf_avatar.pack(side="left", padx=(0, 14))

        # Action buttons on the right (packed FIRST so right edge never clips!)
        actions_box = ctk.CTkFrame(top, fg_color="transparent")
        actions_box.pack(side="right", anchor="ne", padx=(6, 0), pady=2)

        ctk.CTkButton(actions_box, text="👥 Switch", width=95, height=30, corner_radius=10,
                      font=ctk.CTkFont(size=11, weight="bold"), fg_color=ACCENT_CYAN,
                      hover_color=ACCENT_BLUE, text_color=BG_MAIN,
                      command=self._open_profile_switcher).pack(side="left", padx=2)

        ctk.CTkButton(actions_box, text="+ New", width=74, height=30, corner_radius=10,
                      font=ctk.CTkFont(size=11, weight="bold"), fg_color=BG_CARD_INNER,
                      hover_color=BORDER_GLOW, text_color=TEXT_PRIMARY,
                      command=self._create_new_profile_prompt).pack(side="left", padx=2)

        ctk.CTkButton(actions_box, text="✎ Edit", width=70, height=30, corner_radius=10,
                      font=ctk.CTkFont(size=11, weight="bold"), fg_color=BG_CARD_INNER,
                      hover_color=BORDER_GLOW, text_color=TEXT_SECONDARY,
                      command=self._edit_name).pack(side="left", padx=2)

        # Info in the middle (fills remaining space)
        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        self.pf_name_lbl = ctk.CTkLabel(info, text=self._user_name, font=ctk.CTkFont(size=22, weight="bold"),
                                        text_color=TEXT_PRIMARY, anchor="w")
        self.pf_name_lbl.pack(anchor="w")
        self.pf_role_lbl = ctk.CTkLabel(info, text=self._role_text(), font=ctk.CTkFont(size=12),
                                        text_color=ACCENT_CYAN, anchor="w")
        self.pf_role_lbl.pack(anchor="w", pady=(2, 4))
        ctk.CTkLabel(info, text=self._device_text(), font=ctk.CTkFont(size=10),
                     text_color=TEXT_MUTED, anchor="w").pack(anchor="w")

        streak_row = ctk.CTkFrame(hero, fg_color=BG_CARD_INNER, corner_radius=12)
        streak_row.pack(fill="x", padx=18, pady=(0, 18))
        self.pf_streak_lbl = ctk.CTkLabel(streak_row, text="🔥 -- Day Activity Streak!",
                                          font=ctk.CTkFont(size=13, weight="bold"), text_color=ACCENT_AMBER)
        self.pf_streak_lbl.pack(side="left", padx=14, pady=12)

        pills_row = ctk.CTkFrame(streak_row, fg_color="transparent")
        pills_row.pack(side="right", padx=10)
        self.pf_day_pills = []
        for letter in self.DAY_LETTERS:
            pill = ctk.CTkFrame(pills_row, width=34, height=26, corner_radius=13, fg_color=BG_PILL)
            pill.pack(side="left", padx=3, pady=10)
            lbl = ctk.CTkLabel(pill, text=letter, font=ctk.CTkFont(size=11, weight="bold"),
                               text_color=TEXT_MUTED, fg_color="transparent")
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            self.pf_day_pills.append((pill, lbl))

        # ── One-click ergonomic presets ──────────────────────────────────────
        presets = card(left_col)
        ctk.CTkLabel(presets, text="ONE-CLICK ERGONOMIC PRESETS", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 6))
        ctk.CTkLabel(presets, text="Instant calibration switch for different activities:",
                     font=ctk.CTkFont(size=12), text_color=TEXT_PRIMARY).pack(anchor="w", padx=18, pady=(0, 12))

        self.pf_preset_btns = {}
        for p in self.PRESETS:
            row = ctk.CTkFrame(presets, fg_color=BG_CARD_INNER, corner_radius=12)
            row.pack(fill="x", padx=18, pady=(0, 10))
            row.grid_columnconfigure(0, weight=1)
            txt = ctk.CTkFrame(row, fg_color="transparent")
            txt.grid(row=0, column=0, sticky="w", padx=16, pady=14)
            ctk.CTkLabel(txt, text=p["name"], font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(txt, text=self._preset_desc(p), font=ctk.CTkFont(size=11),
                         text_color=TEXT_MUTED, anchor="w").pack(anchor="w", pady=(4, 0))
            btn = ctk.CTkButton(row, text="Activate", width=104, height=34, corner_radius=8,
                                font=ctk.CTkFont(size=12, weight="bold"), fg_color=ACCENT_CYAN,
                                hover_color=ACCENT_BLUE, text_color=BG_MAIN,
                                command=lambda pr=p: self._apply_preset(pr))
            btn.grid(row=0, column=1, padx=16)
            self.pf_preset_btns[p["name"]] = btn
        ctk.CTkFrame(presets, fg_color="transparent", height=6).pack()

        # ── Lifetime ergonomic telemetry (2 x 2 tiles) ───────────────────────
        tele = card(right_col)
        ctk.CTkLabel(tele, text="LIFETIME ERGONOMIC TELEMETRY", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 10))
        grid = ctk.CTkFrame(tele, fg_color="transparent")
        grid.pack(fill="x", padx=13, pady=(0, 14))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="tile")

        self.pf_tiles = {}
        for key, sub, color, r, c in [
            ("hands_free", "Active Hands-Free Work Time",        ACCENT_CYAN,   0, 0),
            ("clicks",     "Dwell Clicks Executed Hands-Free",   ACCENT_GREEN,  0, 1),
            ("posture",    "Average Ergonomic Posture Adherence", ACCENT_PURPLE, 1, 0),
            ("blinks",     "Blinks Monitored & Analyzed",        ACCENT_AMBER,  1, 1),
        ]:
            tile = ctk.CTkFrame(grid, fg_color=BG_CARD_INNER, corner_radius=12)
            tile.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            val = ctk.CTkLabel(tile, text="--", font=ctk.CTkFont(size=22, weight="bold"),
                               text_color=color, anchor="w")
            val.pack(anchor="w", padx=16, pady=(14, 2))
            ctk.CTkLabel(tile, text=sub, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED,
                         anchor="w", justify="left", wraplength=170).pack(anchor="w", padx=16, pady=(0, 14))
            self.pf_tiles[key] = val

        # ── Daily ergonomic goals (live progress bars) ───────────────────────
        goals = card(right_col)
        ctk.CTkLabel(goals, text="DAILY ERGONOMIC GOALS", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 10))
        self.pf_goals = {}
        for key, title in [("breaks",  "20-20-20 Away-Gaze Cycles"),
                           ("blink",   "Blink Rate Maintenance"),
                           ("posture", "Turtle Neck Zero-Tolerance")]:
            row = ctk.CTkFrame(goals, fg_color=BG_CARD_INNER, corner_radius=12)
            row.pack(fill="x", padx=18, pady=(0, 10))
            head = ctk.CTkFrame(row, fg_color="transparent")
            head.pack(fill="x", padx=16, pady=(12, 6))
            ctk.CTkLabel(head, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TEXT_PRIMARY).pack(side="left")
            status = ctk.CTkLabel(head, text="--", font=ctk.CTkFont(size=12, weight="bold"),
                                  text_color=TEXT_MUTED)
            status.pack(side="right")
            bar = ctk.CTkProgressBar(row, height=8, fg_color=BG_PILL, progress_color=TEXT_MUTED)
            bar.set(0)
            bar.pack(fill="x", padx=16, pady=(0, 14))
            self.pf_goals[key] = (status, bar)
        ctk.CTkFrame(goals, fg_color="transparent", height=4).pack()

        # ── Presentation Mode: Floating Face Cam (Always-on-Top) ────────────
        pres = card(right_col)
        ctk.CTkLabel(pres, text="PRESENTATION & SCREEN RECORDING", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=18, pady=(18, 6))
        
        pres_row = ctk.CTkFrame(pres, fg_color=BG_CARD_INNER, corner_radius=12)
        pres_row.pack(fill="x", padx=18, pady=(0, 14))
        pres_row.grid_columnconfigure(0, weight=1)
        
        pres_txt = ctk.CTkFrame(pres_row, fg_color="transparent")
        pres_txt.grid(row=0, column=0, sticky="w", padx=16, pady=12)
        
        ctk.CTkLabel(pres_txt, text="📹 Floating Face Cam (Always-on-Top)", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(pres_txt, text="Pop up a small square live camera overlay with real-time gaze tracking that stays visible over PowerPoint and external apps during screen recording.",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, anchor="w", wraplength=270, justify="left").pack(anchor="w", pady=(4, 0))
        
        self.face_cam_switch = ctk.CTkSwitch(
            pres_row, text="", width=44,
            variable=self._floating_cam_var,
            command=self._toggle_floating_face_cam,
            progress_color=ACCENT_CYAN
        )
        self.face_cam_switch.grid(row=0, column=1, padx=(0, 16))

        return page

    # ──────────────────────────────────────────────────────────────────────────
    #  Persistent Bottom Telemetry HUD
    # ──────────────────────────────────────────────────────────────────────────
    def _build_bottom_telemetry_hud(self):
        hud = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=40)
        hud.grid(row=1, column=0, columnspan=2, sticky="ew")
        hud.grid_propagate(False)

        ctk.CTkFrame(hud, fg_color=BORDER_SUBTLE, height=1).place(x=0, y=0, relwidth=1.0)

        self.hud_sys_dot = ctk.CTkLabel(hud, text="●", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED)
        self.hud_sys_dot.pack(side="left", padx=(20, 6))
        self.hud_sys_txt = ctk.CTkLabel(hud, text="System: Standby", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_SECONDARY)
        self.hud_sys_txt.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(hud, text="|", font=ctk.CTkFont(size=12), text_color=BORDER_SUBTLE).pack(side="left", padx=4)

        self.hud_blink_txt = ctk.CTkLabel(hud, text="Blink Rate: -- BPM (Measuring)", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.hud_blink_txt.pack(side="left", padx=14)

        ctk.CTkLabel(hud, text="|", font=ctk.CTkFont(size=12), text_color=BORDER_SUBTLE).pack(side="left", padx=4)

        self.hud_posture_txt = ctk.CTkLabel(hud, text="Posture: -- (No face detected)", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.hud_posture_txt.pack(side="left", padx=14)

        ctk.CTkLabel(hud, text="|", font=ctk.CTkFont(size=12), text_color=BORDER_SUBTLE).pack(side="left", padx=4)

        self.hud_preset_txt = ctk.CTkLabel(hud, text=f"Preset: {self._active_preset}", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY)
        self.hud_preset_txt.pack(side="left", padx=14)

        self._session_lbl = ctk.CTkLabel(hud, text="Session:  00:00:00", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY)
        self._session_lbl.pack(side="right", padx=24)

    # ──────────────────────────────────────────────────────────────────────────
    #  Controls & Callbacks
    # ──────────────────────────────────────────────────────────────────────────
    def toggle_mouse_event(self):
        self._mouse_on = bool(self._mouse_enabled.get())   # keep the camera thread's mirror in sync
        if self._mouse_on:
            self.tracking_status_card.set_status("Active", color=ACCENT_GREEN)
            self.hud_sys_dot.configure(text_color=ACCENT_GREEN)
            self.hud_sys_txt.configure(text="System: Active", text_color=TEXT_PRIMARY)
            if not hasattr(self, 'dock') or not self.dock.winfo_exists():
                self.dock = FloatingDock(self, self._click_mode)
                self.on_dock_move(self._dock_pos_x) 
        else:
            self.tracking_status_card.set_status("Paused", color=TEXT_MUTED)
            self.hud_sys_dot.configure(text_color=TEXT_MUTED)
            self.hud_sys_txt.configure(text="System: Standby", text_color=TEXT_SECONDARY)
            if self._is_dragging:
                pyautogui.mouseUp()
                self._is_dragging = False
                self._click_mode.set("Left")
                self.click_status_card.set_status("Dropped!", color=TEXT_MUTED)
            if hasattr(self, 'dock') and self.dock.winfo_exists():
                self.dock.destroy()
            if hasattr(self, 'keyboard') and self.keyboard.winfo_exists():
                self.keyboard.destroy()

    # ──────────────────────────────────────────────────────────────────────────
    #  Profile (persisted to vision360_profile.json next to this script)
    # ──────────────────────────────────────────────────────────────────────────
    XP_PER_LEVEL      = 500
    DAILY_BREAK_GOAL  = 8        # 20-20-20 cycles per day
    BLINK_TARGET_BPM  = 14.0     # "healthy" threshold used by the gauge too
    DAY_LETTERS       = "MTWTFSS"
    PRESETS = [
        {"name": "Deep Focus & Coding",    "tag": "Steady cursor",    "smoothing": 0.35, "sensitivity": 0.22, "scroll": 280},
        {"name": "Casual Browsing & Web",  "tag": "Snappy cursor",    "smoothing": 0.70, "sensitivity": 0.20, "scroll": 420},
        {"name": "Precision Motor Assist", "tag": "Tremor dampening", "smoothing": 0.25, "sensitivity": 0.40, "scroll": 200},
    ]

    def _load_profile(self, profile_id=None):
        """Load saved profile (multi-user workstation aware); missing or corrupt data falls back to clean state."""
        today = datetime.date.today()
        
        # 1. Attempt to load multi-profile store
        multi_data = None
        try:
            if hasattr(self, "_profiles_path") and self._profiles_path.exists():
                multi_data = json.loads(self._profiles_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Profiles DB load warning: {e}")
            multi_data = None

        if isinstance(multi_data, dict) and isinstance(multi_data.get("profiles"), dict) and multi_data["profiles"]:
            self._profiles_db = multi_data
            if profile_id and profile_id in self._profiles_db["profiles"]:
                self._active_profile_id = profile_id
            elif self._profiles_db.get("active_id") in self._profiles_db["profiles"]:
                self._active_profile_id = self._profiles_db["active_id"]
            else:
                self._active_profile_id = next(iter(self._profiles_db["profiles"].keys()))
        else:
            # 2. Check legacy single profile
            legacy = {}
            try:
                if self._profile_path.exists():
                    legacy = json.loads(self._profile_path.read_text(encoding="utf-8"))
                if not isinstance(legacy, dict):
                    legacy = {}
            except Exception as e:
                print(f"Legacy profile load failed: {e}")
                legacy = {}
            
            init_name = (str(legacy.get("name") or "Bunny").strip() or "Bunny")[:24]
            legacy["name"] = init_name
            self._active_profile_id = "user_default"
            self._profiles_db = {
                "active_id": self._active_profile_id,
                "profiles": {
                    self._active_profile_id: legacy
                }
            }

        d = self._profiles_db.get("profiles", {}).get(self._active_profile_id, {})
        if not isinstance(d, dict):
            d = {}

        self._user_name = (str(d.get("name") or "Guest").strip() or "Guest")[:24]
        self._player_xp = int(_safe_num(d, "xp", 0, 0))
        self._player_level = self._level_for_xp(self._player_xp)

        # lifetime totals (bases; this run's numbers are added on top)
        self._lifetime_clicks      = int(_safe_num(d, "lifetime_clicks", 0, 0))
        self._lifetime_blinks_base = int(_safe_num(d, "lifetime_blinks", 0, 0))
        self._hands_free_base      = _safe_num(d, "hands_free_secs", 0.0, 0.0)
        self._posture_good_base    = _safe_num(d, "posture_good_secs", 0.0, 0.0)
        self._posture_total_base   = _safe_num(d, "posture_total_secs", 0.0, 0.0)

        # motor settings + which preset is active
        st = d.get("settings") if isinstance(d.get("settings"), dict) else {}
        self._sensitivity  = _safe_num(st, "sensitivity", 0.25, 0.15, 0.45)
        self._smoothing    = _safe_num(st, "smoothing", 0.5, 0.1, 1.0)
        self._mouth_thresh = _safe_num(st, "mouth_thresh", 0.40, 0.20, 0.70)
        self._scroll_speed = int(_safe_num(st, "scroll_speed", 360, 100, 1000))
        self._dwell_time   = float(_safe_num(st, "dwell_time", 1.0, 0.3, 3.0))
        self._dwell_radius = int(_safe_num(st, "dwell_radius", 25, 10, 60))
        self._ear_close_thresh  = float(_safe_num(st, "ear_close_thresh", 0.19, 0.10, 0.35))
        self._ear_reopen_thresh = float(_safe_num(st, "ear_reopen_thresh", 0.23, 0.14, 0.40))
        self._ear_baseline      = float(_safe_num(st, "ear_baseline", 0.28, 0.15, 0.50))
        self._eye_width_cm      = float(_safe_num(st, "eye_width_cm", 9.0, 6.0, 14.0))
        preset = d.get("preset")
        self._active_preset = preset if isinstance(preset, str) and preset else "Default"

        # activity calendar (streak + weekly pills)
        self._first_run = _parse_date(d.get("first_run")) or today
        self._active_dates = set()
        raw_dates = d.get("active_dates")
        for s in (raw_dates if isinstance(raw_dates, list) else []):
            dt = _parse_date(s)
            if dt and dt <= today:
                self._active_dates.add(dt)
        self._active_dates.add(today)       # opening the app counts as activity today

        # today's goals (reset automatically on a new day)
        daily = d.get("daily") if isinstance(d.get("daily"), dict) else {}
        self._day_key = today
        if _parse_date(daily.get("date")) == today:
            self._loaded_breaks     = int(_safe_num(daily, "breaks", 0, 0))
            self._daily_good_base   = _safe_num(daily, "good_secs", 0.0, 0.0)
            self._daily_total_base  = _safe_num(daily, "total_secs", 0.0, 0.0)
        else:
            self._loaded_breaks, self._daily_good_base, self._daily_total_base = 0, 0.0, 0.0
        self._away_gazes_done = self._loaded_breaks
        self._day_good0 = 0.0      # session posture counters at the start of "today"
        self._day_total0 = 0.0
        self._last_save_t = time.time()

    def _save_profile(self):
        try:
            d_good, d_total = self._daily_posture()
            payload = {
                "name": self._user_name,
                "xp": self._player_xp,
                "preset": self._active_preset,
                "settings": {
                    "sensitivity": round(self._sensitivity, 3),
                    "smoothing": round(self._smoothing, 3),
                    "mouth_thresh": round(self._mouth_thresh, 3),
                    "scroll_speed": int(self._scroll_speed),
                    "dwell_time": round(float(self._dwell_time), 2),
                    "dwell_radius": int(self._dwell_radius),
                    "ear_close_thresh": round(getattr(self, '_ear_close_thresh', 0.19), 3),
                    "ear_reopen_thresh": round(getattr(self, '_ear_reopen_thresh', 0.23), 3),
                    "ear_baseline": round(getattr(self, '_ear_baseline', 0.28), 3),
                    "eye_width_cm": round(getattr(self, '_eye_width_cm', 9.0), 2),
                },
                "first_run": self._first_run.isoformat(),
                "active_dates": sorted(x.isoformat() for x in self._active_dates)[-120:],
                "lifetime_clicks": self._lifetime_clicks,
                "lifetime_blinks": self._lifetime_blinks(),
                "hands_free_secs": round(self._hands_free_total(), 1),
                "posture_good_secs": round(self._posture_good_base + self._posture_good_secs, 1),
                "posture_total_secs": round(self._posture_total_base + self._posture_total_secs, 1),
                "daily": {
                    "date": self._day_key.isoformat(),
                    "breaks": self._away_gazes_done,
                    "good_secs": round(d_good, 1),
                    "total_secs": round(d_total, 1),
                },
            }
            if not hasattr(self, "_profiles_db") or not isinstance(self._profiles_db, dict):
                self._profiles_db = {"active_id": self._active_profile_id, "profiles": {}}
            self._profiles_db.setdefault("profiles", {})[self._active_profile_id] = payload
            self._profiles_db["active_id"] = self._active_profile_id

            if hasattr(self, "_profiles_path"):
                tmp_multi = self._profiles_path.with_suffix(".tmp")
                tmp_multi.write_text(json.dumps(self._profiles_db, indent=2), encoding="utf-8")
                tmp_multi.replace(self._profiles_path)

            tmp = self._profile_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self._profile_path)
        except Exception as e:
            print(f"Profile save failed: {e}")
        self._last_save_t = time.time()

    def switch_profile(self, profile_id):
        if not hasattr(self, "_profiles_db") or profile_id not in self._profiles_db.get("profiles", {}):
            return
        
        # 1. Save current profile
        self._save_profile()
        
        # 2. Reset session dynamic counters for new user
        self._session_blinks = 0
        self._posture_good_secs = 0.0
        self._posture_total_secs = 0.0
        self._hands_free_secs = 0.0
        
        # 3. Switch active user and reload
        self._active_profile_id = profile_id
        self._load_profile(profile_id=profile_id)
        
        # 4. Sync sliders if they exist
        if hasattr(self, "sensitivity_slider"):
            try:
                self.sensitivity_slider.set_value(self._sensitivity)
                self.smoothing_slider.set_value(self._smoothing)
                self.scroll_speed_slider.set_value(self._scroll_speed)
            except Exception:
                pass

        if hasattr(self, "dwell_time_slider"):
            try:
                self.dwell_time_slider.set_value(self._dwell_time)
                self.dwell_radius_slider.set_value(self._dwell_radius)
            except Exception:
                pass
        
        # 5. Persist switch
        self._save_profile()
        
        # 6. Refresh UI across all components
        self._refresh_profile_widgets()
        self._switch_tab(self._current_tab)

    def create_new_profile(self, name: str):
        name = (name or "").strip()[:24]
        if not name:
            return
        pid = f"user_{int(time.time() * 1000)}"
        today = datetime.date.today()
        new_prof = {
            "name": name,
            "xp": 0,
            "preset": "Default",
            "settings": {
                "sensitivity": 0.25,
                "smoothing": 0.5,
                "mouth_thresh": 0.40,
                "scroll_speed": 360,
                "dwell_time": 1.0,
                "dwell_radius": 25,
            },
            "first_run": today.isoformat(),
            "active_dates": [today.isoformat()],
            "lifetime_clicks": 0,
            "lifetime_blinks": 0,
            "hands_free_secs": 0.0,
            "posture_good_secs": 0.0,
            "posture_total_secs": 0.0,
            "daily": {
                "date": today.isoformat(),
                "breaks": 0,
                "good_secs": 0.0,
                "total_secs": 0.0,
            },
        }
        self._profiles_db.setdefault("profiles", {})[pid] = new_prof
        self.switch_profile(pid)

    def start_guest_mode(self):
        profiles = self._profiles_db.setdefault("profiles", {})
        guest_pid = None
        for pid, p in profiles.items():
            if pid == "guest_mode" or p.get("name") == "Guest User":
                guest_pid = pid
                break
        if not guest_pid:
            today = datetime.date.today()
            guest_pid = "guest_mode"
            profiles[guest_pid] = {
                "name": "Guest User",
                "xp": 0,
                "preset": "Default",
                "settings": {
                    "sensitivity": 0.25,
                    "smoothing": 0.5,
                    "mouth_thresh": 0.40,
                    "scroll_speed": 360,
                    "dwell_time": 1.0,
                    "dwell_radius": 25,
                },
                "first_run": today.isoformat(),
                "active_dates": [today.isoformat()],
                "lifetime_clicks": 0,
                "lifetime_blinks": 0,
                "hands_free_secs": 0.0,
                "posture_good_secs": 0.0,
                "posture_total_secs": 0.0,
                "daily": {
                    "date": today.isoformat(),
                    "breaks": 0,
                    "good_secs": 0.0,
                    "total_secs": 0.0,
                },
            }
        self.switch_profile(guest_pid)

    def delete_profile(self, profile_id: str):
        profiles = self._profiles_db.get("profiles", {})
        if len(profiles) <= 1:
            return False
        if profile_id in profiles:
            del profiles[profile_id]
            if self._active_profile_id == profile_id:
                next_id = next(iter(profiles.keys()))
                self.switch_profile(next_id)
            else:
                self._save_profile()
            return True
        return False

    def _open_profile_switcher(self):
        try:
            if hasattr(self, "_switcher_dialog") and self._switcher_dialog and self._switcher_dialog.winfo_exists():
                self._switcher_dialog.lift()
                self._switcher_dialog.focus_force()
                return
            self._switcher_dialog = ProfileSwitcherDialog(self, self)
        except Exception as e:
            print(f"Failed to open profile switcher: {e}")

    def _create_new_profile_prompt(self):
        val = ctk.CTkInputDialog(text="Enter new user display name:", title="New Profile").get_input()
        if val and val.strip():
            self.create_new_profile(val.strip())

    def _open_feature_guide(self):
        """Opens or lifts the Vision360 Feature Handbook and User Guide dialog."""
        try:
            if hasattr(self, "_feature_guide_dialog") and self._feature_guide_dialog and self._feature_guide_dialog.winfo_exists():
                self._feature_guide_dialog.lift()
                self._feature_guide_dialog.focus_force()
                return
            self._feature_guide_dialog = FeatureGuideModal(self)
        except Exception as e:
            print(f"Failed to open feature guide: {e}")

    def _toggle_floating_face_cam(self):
        """Toggles the Always-on-Top Floating Face Cam for screen recordings and presentations."""
        try:
            if self._floating_cam_var.get():
                if self._floating_face_cam is None or not self._floating_face_cam.winfo_exists():
                    self._floating_face_cam = FloatingFaceCamOverlay(self, on_close_callback=self._on_floating_face_cam_closed)
                else:
                    self._floating_face_cam.lift()
            else:
                if self._floating_face_cam is not None:
                    try:
                        self._floating_face_cam.close()
                    except Exception:
                        pass
                    self._floating_face_cam = None
        except Exception as e:
            print(f"Failed to toggle floating face cam: {e}")

    def _on_floating_face_cam_closed(self):
        """Called when user closes the floating face cam via its top-right X button."""
        self._floating_cam_var.set(False)
        self._floating_face_cam = None

    # ── derived values (all computed from real counters) ─────────────────────
    def _lifetime_blinks(self):
        return self._lifetime_blinks_base + self._session_blinks

    def _hands_free_total(self):
        return self._hands_free_base + self._hands_free_secs

    def _daily_posture(self):
        """(good_secs, total_secs) of posture tracking for today."""
        return (self._daily_good_base + self._posture_good_secs - self._day_good0,
                self._daily_total_base + self._posture_total_secs - self._day_total0)

    def _streak(self):
        d, n = self._day_key, 0
        while d in self._active_dates:
            n += 1
            d -= datetime.timedelta(days=1)
        return n

    def _check_day_rollover(self):
        """Called every second: starts a fresh day (goals reset, streak extends) after midnight."""
        today = datetime.date.today()
        if today == self._day_key:
            return
        self._day_key = today
        self._active_dates.add(today)
        self._daily_good_base = self._daily_total_base = 0.0
        self._day_good0, self._day_total0 = self._posture_good_secs, self._posture_total_secs
        self._away_gazes_done = 0
        self._save_profile()

    def _level_for_xp(self, xp):
        return 1 + int(xp) // self.XP_PER_LEVEL

    def _rank_title(self):
        lvl = self._level_for_xp(self._player_xp)
        title = "Rookie"
        for min_lvl, name in [(1, "Rookie"), (3, "Optic Scout"), (5, "Optic Athlete"), (8, "Vision Master")]:
            if lvl >= min_lvl:
                title = name
        return title

    def _rank_line(self):
        to_next = self.XP_PER_LEVEL - (self._player_xp % self.XP_PER_LEVEL)
        return f"Rank: {self._rank_title()}  ·  {self._player_xp} XP  ·  {to_next} XP to next level"

    def _role_text(self):
        in_level = self._player_xp % self.XP_PER_LEVEL
        return f"Level {self._level_for_xp(self._player_xp)} · {self._rank_title()} · {in_level}/{self.XP_PER_LEVEL} XP"

    def _device_text(self):
        node = platform.node() or "This PC"
        return f"Device: {node} · {platform.system()} {platform.release()}  ·  Member since {self._first_run.strftime('%b %Y')}"

    def _initials(self):
        parts = self._user_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self._user_name[:2].upper() or "?"

    def _preset_desc(self, p):
        return f"{p['tag']} ({p['smoothing']:.2f}) · Sensitivity {p['sensitivity']:.2f} · Scroll {p['scroll']}"

    # ── actions ──────────────────────────────────────────────────────────────
    def _start_ear_calibration(self):
        """Item 7: 3-second 'eyes open' calibration that sets threshold at 70% of open-eye EAR."""
        if getattr(self, '_ear_calibrating', False):
            return
        self._ear_calibrating = True
        self._ear_calib_samples = []
        if hasattr(self, 'calib_ear_btn'):
            self.calib_ear_btn.configure(text="⏳ Calibrating (3s)...", fg_color=ACCENT_AMBER)
        self._ts_status("🎯 Blink Calibration: Keep eyes open naturally for 3 seconds...", color=ACCENT_CYAN)

        def _finish_calib():
            self._ear_calibrating = False
            samples = getattr(self, '_ear_calib_samples', [])
            if samples:
                avg_open_ear = float(sum(samples) / len(samples))
                self._ear_baseline = avg_open_ear
                # Set close threshold at 70% of open EAR, reopen with 0.04 hysteresis
                self._ear_close_thresh = max(0.14, min(0.30, avg_open_ear * 0.70))
                self._ear_reopen_thresh = max(0.18, min(0.34, self._ear_close_thresh + 0.04))
                txt = f"✓ Calibrated ({self._ear_close_thresh:.2f})"
                status_msg = f"✓ Calibrated: Open EAR {avg_open_ear:.2f} → Threshold {self._ear_close_thresh:.2f}"
                col = ACCENT_GREEN
                self._save_profile()
            else:
                txt = "Calibrate (3s)"
                status_msg = "⚠️ Calibration failed: No face detected. Try again."
                col = ACCENT_RED
            if hasattr(self, 'calib_ear_btn'):
                self.calib_ear_btn.configure(text=txt, fg_color=BG_SURFACE)
            self._ts_status(status_msg, color=col)

        self.after(3000, _finish_calib)

    def _apply_preset(self, p):
        """Apply a preset to the live motor settings and move the Motor-page sliders to match."""
        self._sensitivity = p["sensitivity"]
        self._smoothing = p["smoothing"]
        self._scroll_speed = p["scroll"]
        self.sensitivity_slider.set_value(self._sensitivity)
        self.smoothing_slider.set_value(self._smoothing)
        self.scroll_speed_slider.set_value(self._scroll_speed)
        self._active_preset = p["name"]
        self._save_profile()
        self._refresh_profile_widgets()

    def _mark_custom(self):
        """Any manual slider change means the settings no longer match a preset."""
        if self._active_preset != "Custom":
            self._active_preset = "Custom"
            self._refresh_profile_widgets()

    def _edit_name(self):
        val = ctk.CTkInputDialog(text="Enter your display name:", title="Edit name").get_input()
        if val is None:
            return
        self._user_name = val.strip()[:24] or "Guest"
        self._save_profile()
        self._refresh_profile_widgets()
        self._switch_tab(self._current_tab)      # refreshes the header title too

    # ── cached widget updaters (skip redraws when nothing changed) ───────────
    def _set_btn(self, btn, text, fg):
        key = (text, fg)
        if getattr(btn, "_v360_last", None) == key:
            return
        btn._v360_last = key
        btn.configure(text=text, fg_color=fg)

    def _set_bar(self, bar, frac, color):
        key = (round(frac, 2), color)
        if getattr(bar, "_v360_last", None) == key:
            return
        bar._v360_last = key
        bar.configure(progress_color=color)
        bar.set(max(0.0, min(1.0, frac)))

    def _set_pill(self, pill, fg, border):
        key = (fg, border)
        if getattr(pill, "_v360_last", None) == key:
            return
        pill._v360_last = key
        pill.configure(fg_color=fg, border_width=2 if border else 0, border_color=border or fg)

    def _refresh_profile_widgets(self):
        """Push real profile / gamification / goal values into every widget that shows them."""
        if not (hasattr(self, "pf_tiles") and hasattr(self, "hud_preset_txt")):
            return                                    # UI not fully built yet
        lvl = self._level_for_xp(self._player_xp)
        self._player_level = lvl
        rank = self._rank_title()
        initials = self._initials()

        # sidebar pill, EyeGym card, bottom HUD
        self._set_label(self.sb_name_lbl, self._user_name)
        self._set_label(self.sb_avatar, initials)
        self._set_label(self.sb_level_lbl, f"Lvl {lvl} · {rank}")
        self._set_label(self.gym_level_lbl, f"LEVEL {lvl} · {rank.upper()}")
        self._set_label(self.gym_rank_lbl, self._rank_line())
        self._set_label(self.hud_preset_txt, f"Preset: {self._active_preset}")

        # hero card
        self._set_label(self.pf_avatar, initials)
        self._set_label(self.pf_name_lbl, self._user_name)
        self._set_label(self.pf_role_lbl, self._role_text())
        self._set_label(self.pf_streak_lbl, f"🔥 {self._streak()}-Day Activity Streak!")
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        for i, (pill, lbl) in enumerate(self.pf_day_pills):
            day = monday + datetime.timedelta(days=i)
            active = day in self._active_dates
            self._set_pill(pill, ACCENT_GREEN if active else BG_PILL, ACCENT_CYAN if day == today else None)
            self._set_label(lbl, self.DAY_LETTERS[i], TEXT_PRIMARY if active else TEXT_MUTED)

        # presets
        for name, btn in self.pf_preset_btns.items():
            active = (name == self._active_preset)
            self._set_btn(btn, "✓ Active" if active else "Activate", ACCENT_GREEN if active else ACCENT_CYAN)

        # lifetime telemetry tiles
        hf = self._hands_free_total()
        self._set_label(self.pf_tiles["hands_free"], f"{hf / 3600.0:.1f} hrs" if hf >= 3600 else f"{int(hf // 60)} min")
        self._set_label(self.pf_tiles["clicks"], f"{self._lifetime_clicks:,}")
        life_good = self._posture_good_base + self._posture_good_secs
        life_total = self._posture_total_base + self._posture_total_secs
        self._set_label(self.pf_tiles["posture"], f"{life_good / life_total * 100.0:.1f}%" if life_total >= 5.0 else "--")
        self._set_label(self.pf_tiles["blinks"], f"{self._lifetime_blinks():,}")

        # daily goals
        n, goal = self._away_gazes_done, self.DAILY_BREAK_GOAL
        s, b = self.pf_goals["breaks"]
        self._set_label(s, f"{n} / {goal} Done ({min(100, int(n / goal * 100))}%)", ACCENT_CYAN)
        self._set_bar(b, n / goal, ACCENT_CYAN)

        # EyeRest dynamic break cycles
        if hasattr(self, 'away_gaze_lbl') and self.away_gaze_lbl.winfo_exists():
            self._set_label(self.away_gaze_lbl, f"Away-Gaze Cycles: {self._away_gazes_done} Completed")
        if hasattr(self, 'stat_breaks_lbl') and self.stat_breaks_lbl.winfo_exists():
            self._set_label(self.stat_breaks_lbl, f"{self._away_gazes_done} / {goal} Cycles")

        bpm = self._current_bpm
        s, b = self.pf_goals["blink"]
        if bpm is None:
            txt, col, frac = "-- (Measuring)", TEXT_MUTED, 0.0
        elif bpm >= self.BLINK_TARGET_BPM:
            txt, col, frac = f"{int(round(bpm))} BPM (Target Met)", ACCENT_GREEN, 1.0
        else:
            txt, col, frac = (f"{int(round(bpm))} BPM (Below Target)",
                              ACCENT_AMBER if bpm >= 10 else ACCENT_RED, bpm / self.BLINK_TARGET_BPM)
        self._set_label(s, txt, col)
        self._set_bar(b, frac, col)

        d_good, d_total = self._daily_posture()
        s, b = self.pf_goals["posture"]
        if d_total < 5.0:
            txt, col, frac = "-- (Measuring)", TEXT_MUTED, 0.0
        else:
            pct = int(d_good / d_total * 100)
            txt, col, frac = (f"{pct}% Upright Today",
                              ACCENT_PURPLE if pct >= 80 else (ACCENT_AMBER if pct >= 50 else ACCENT_RED), pct / 100.0)
        self._set_label(s, txt, col)
        self._set_bar(b, frac, col)

    def _on_close(self):
        """Stop the camera thread cleanly, release any held mouse button, save, exit."""
        self._cam_running = False
        if hasattr(self, '_active_cap') and self._active_cap is not None:
            try:
                self._active_cap.release()
            except Exception:
                pass
            self._active_cap = None
        if getattr(self, "_floating_face_cam", None) is not None:
            try: self._floating_face_cam.destroy()
            except Exception: pass
            self._floating_face_cam = None
        if getattr(self, "_feature_guide_dialog", None) is not None:
            try: self._feature_guide_dialog.destroy()
            except Exception: pass
            self._feature_guide_dialog = None
        if self._is_dragging:
            try: pyautogui.mouseUp()
            except Exception: pass
            self._is_dragging = False
        self._save_profile()
        t = self._cam_thread
        if t is not None and t.is_alive():
            t.join(timeout=1.0)
        try:
            self.destroy()
        except Exception:
            pass
        # Immediate clean exit to release Windows camera handles and prevent zombie processes
        try:
            import os
            os._exit(0)
        except Exception:
            pass

    def on_sensitivity_change(self, v): self._sensitivity = v; self._mark_custom()
    def on_smoothing_change(self, v): self._smoothing = v; self._mark_custom()
    def on_mouth_thresh_change(self, v): self._mouth_thresh = v
    def on_scroll_speed_change(self, v): self._scroll_speed = int(v); self._mark_custom()
    def on_break_interval_change(self, v):
        """Fires when the user adjusts the Break Timer slider."""
        # Convert slider value (minutes) directly into seconds
        new_interval_secs = int(v) * 60
        self._break_interval_mins = int(v)
        
        # Instantly reset the current countdown to exactly match the slider
        self._cycle_20_20 = new_interval_secs
        
        # Sync the specific Cyberpunk timer Canvas to the new maximum total immediately
        if hasattr(self, 'rule_2020_gauge'):
             self.rule_2020_gauge.set_timer(new_interval_secs, new_interval_secs)
             
        self._break_active = False

    def _start_wellness_cycle(self):
        """20-20-20 Rule countdown timer loop."""
        # 1. PAUSE the clock while the break notification is on the screen!
        if getattr(self, '_break_active', False):
            self.after(1000, self._start_wellness_cycle)
            return
            
        # 2. Count down normally
        if self._cycle_20_20 > 0:
            self._cycle_20_20 -= 1
        else:
            # 3. Time is up! Lock the gate and spawn the notification
            self._break_active = True  
            self._cycle_20_20 = getattr(self, '_break_interval_mins', 20.0) * 60.0 
            self._away_gazes_done += 1
            self._player_xp += 50
            if hasattr(self, 'away_gaze_lbl') and self.away_gaze_lbl.winfo_exists():
                self.away_gaze_lbl.configure(text=f"Away-Gaze Cycles: {self._away_gazes_done} Completed")
            if hasattr(self, 'stat_breaks_lbl') and self.stat_breaks_lbl.winfo_exists():
                self.stat_breaks_lbl.configure(text=f"{self._away_gazes_done} / {getattr(self, 'DAILY_BREAK_GOAL', 8)} Cycles")
            self._refresh_profile_widgets()
            self._save_profile()
            
            self.click_status_card.set_status("Break Time!", color=ACCENT_PURPLE)
            
            # Spawn the popup and pass the unlock function for when it finishes
            BreakGatekeeper(self, break_duration=20, on_close=self._end_break)
            
        self.after(1000, self._start_wellness_cycle)

    def trigger_break_now(self):
        """Manually trigger an away-gaze break cycle for testing or ergonomic relief."""
        if not getattr(self, '_break_active', False):
            self._cycle_20_20 = 0

    def _end_break(self):
        """Unlocks the background timer loop after the popup destroys itself."""
        self._break_active = False
        if hasattr(self, 'away_gaze_lbl') and self.away_gaze_lbl.winfo_exists():
            self.away_gaze_lbl.configure(text=f"Away-Gaze Cycles: {self._away_gazes_done} Completed")
        if hasattr(self, 'stat_breaks_lbl') and self.stat_breaks_lbl.winfo_exists():
            self.stat_breaks_lbl.configure(text=f"{self._away_gazes_done} / {getattr(self, 'DAILY_BREAK_GOAL', 8)} Cycles")
        self._refresh_profile_widgets()
        self._save_profile()

    def on_dock_move(self, v):
        self._dock_pos_x = v
        if hasattr(self, 'dock') and self.dock.winfo_exists():
            sw = self.winfo_screenwidth()
            dock_width = 680
            x_pos = int((sw - dock_width) * v)
            self.dock.geometry(f"{dock_width}x50+{x_pos}+25")

    def _start_session_timer(self):
        elapsed = int(time.time() - self._session_start)
        hrs, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self._session_lbl.configure(text=f"Session:  {hrs:02d}:{mins:02d}:{secs:02d}", text_color=TEXT_PRIMARY)
        
        # Sync EyeRest bottom bar session readout
        if hasattr(self, 'session_time_lbl'):
            total_mins = int(elapsed / 60)
            self.session_time_lbl.configure(text=f"Session: {total_mins}m")
            
        # Hands-free time = time the mouse control is actually ON
        tick = time.monotonic()
        last_tick = getattr(self, "_last_tick", None)
        self._last_tick = tick
        if last_tick is not None and self._mouse_on:
            self._hands_free_secs += min(5.0, tick - last_tick)

        self._check_day_rollover()
        # Item 4: Run _refresh_profile_widgets only when Profile page is visible, and slow to once every 3 seconds
        self._profile_refresh_tick = (getattr(self, '_profile_refresh_tick', 0) + 1) % 3
        if self._profile_refresh_tick == 0 and "Profile" in getattr(self, '_current_tab', ''):
            self._refresh_profile_widgets()
        if time.time() - self._last_save_t >= 60:      # autosave once a minute
            self._save_profile()

        self.after(1000, self._start_session_timer)

    # ──────────────────────────────────────────────────────────────────────────
    #  OpenCV & MediaPipe Computer Vision Backend (100% UNTOUCHED)
    # ──────────────────────────────────────────────────────────────────────────
    # ── Camera-thread → Tk bridge (the camera thread calls ONLY these) ───────
    def _ts_status(self, value, color=None):
        """Thread-safe replacement for click_status_card.set_status (last write wins)."""
        with self._status_lock:
            self._pending_status = (value, color)

    def _ts_flash(self, color=ACCENT_RED, duration_ms=300):
        """Thread-safe replacement for click_status_card.flash."""
        with self._status_lock:
            self._pending_flash = (color, duration_ms)

    def _post_ui(self, event):
        """Queue a discrete event for the main thread: ('mode_left',) or ('set_mouse', bool)."""
        self._ui_events.put(event)

    def _drain_ui_events(self):
        """Runs on the Tk main thread (from the poll loop) and applies queued camera-thread requests."""
        with self._status_lock:
            status, self._pending_status = self._pending_status, None
            flash, self._pending_flash = self._pending_flash, None
        if status is not None:
            self.click_status_card.set_status(status[0], status[1])
        if flash is not None:
            self.click_status_card.flash(flash[0], flash[1])
        while True:
            try:
                ev = self._ui_events.get_nowait()
            except queue.Empty:
                break
            if ev[0] == "mode_left":
                self._click_mode.set("Left")
            elif ev[0] == "set_mouse":
                self._mouse_enabled.set(bool(ev[1]))
                self.toggle_mouse_event()

    def _start_camera(self):
        self._cam_running = True
        self._cam_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self._cam_thread.start()
        self._poll_frame_queue()
        self._start_wellness_sync()

    def _camera_loop(self):
        TASK_PATH = resource_path("face_landmarker.task")
        
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(TASK_PATH)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_faces=1,
        )
        
        def _open_camera():
            # Build priority list of device index and backend combinations
            backends = []
            if sys.platform.startswith("win"):
                backends.append((0, cv2.CAP_DSHOW))
                backends.append((0, None))
                backends.append((1, cv2.CAP_DSHOW))
                backends.append((1, None))
            else:
                backends.append((0, None))
                backends.append((1, None))

            for idx, api in backends:
                c = None
                try:
                    c = cv2.VideoCapture(idx, api) if api is not None else cv2.VideoCapture(idx)
                    if c is not None and c.isOpened():
                        c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        # Verify camera can actually capture live frames
                        for _ in range(3):
                            ret, test_frame = c.read()
                            if ret and test_frame is not None and test_frame.size > 0:
                                return c
                            time.sleep(0.04)
                        c.release()
                except (cv2.error, OSError, ValueError):
                    if c is not None:
                        try: c.release()
                        except Exception: pass

            # Default fallback if specific backends were not matched
            try:
                c = cv2.VideoCapture(0)
                if c is not None and c.isOpened():
                    c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return c
            except Exception:
                pass
            return None

        cap = _open_camera()
        self._active_cap = cap
        screen_w, screen_h = pyautogui.size()
        pyautogui.FAILSAFE = False

        smoothed_x, smoothed_y = screen_w/2, screen_h/2
        dwell_x, dwell_y = smoothed_x, smoothed_y
        dwell_start_time = time.monotonic()
        dwell_state = 0
        # Item 12: Removed leftover hardcoded DWELL_RADIUS constant (uses dynamic slider)
        
        mouth_open_start = 0.0
        is_mouth_open = False
        mouth_cooldown = False
        last_scroll_time = 0.0

        blink_closed = False
        consecutive_closed = 0
        recent_blinks = collections.deque()   # timestamps on the *face-time* clock
        face_secs = 0.0                       # seconds the face has actually been on camera
        last_frame_t = None
        smooth_dist = None

        consecutive_read_failures = 0
        last_mp_ts = 0

        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
            while self._cam_running:
                loop_start = time.monotonic()
                if cap is None or not cap.isOpened():
                    consecutive_read_failures += 1
                else:
                    try:
                        success, frame = cap.read()
                        if not success or frame is None or frame.size == 0:
                            consecutive_read_failures += 1
                        else:
                            consecutive_read_failures = 0
                    except (cv2.error, OSError, ValueError):
                        consecutive_read_failures += 1

                if consecutive_read_failures > 0:
                    if consecutive_read_failures >= 10:
                        # Auto-recover camera if feed stalled or disconnected
                        try:
                            if cap is not None:
                                cap.release()
                        except Exception:
                            pass
                        time.sleep(0.4)
                        cap = _open_camera()
                        self._active_cap = cap
                        consecutive_read_failures = 0
                    time.sleep(0.04)
                    continue

                frame = cv2.flip(frame, 1)

                # Item 3: Downscale frame before MediaPipe to optimize CPU & GIL
                fh, fw = frame.shape[:2]
                if fw > 640:
                    scale_mp = 640.0 / fw
                    frame = cv2.resize(frame, (640, int(fh * scale_mp)), interpolation=cv2.INTER_AREA)

                # Ambient Lighting Photometric Sensor (Scene Brightness %)
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    mean_val = float(np.mean(gray))
                    lum_frac = float(np.clip(mean_val / 255.0, 0.0, 1.0))
                    self._ambient_lum = lum_frac
                    self._ambient_brightness_pct = int(lum_frac * 100.0)
                except Exception:
                    pass

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                now = time.monotonic()
                self._frame_times.append(now)
                if len(self._frame_times) >= 6:
                    span = self._frame_times[-1] - self._frame_times[0]
                    if span > 0.05:
                        self._real_fps = float((len(self._frame_times) - 1) / span)

                dt = min(0.5, now - last_frame_t) if last_frame_t is not None else 0.0
                last_frame_t = now
                ts_ms = int(now * 1000)
                if ts_ms <= last_mp_ts:
                    ts_ms = last_mp_ts + 1
                last_mp_ts = ts_ms

                try:
                    t_inf = time.perf_counter()
                    result = landmarker.detect_for_video(mp_image, ts_ms)
                    inf_ms = (time.perf_counter() - t_inf) * 1000.0
                    prev_ms = self._latency_ms
                    self._latency_ms = inf_ms if prev_ms is None else prev_ms * 0.9 + inf_ms * 0.1
                except Exception:
                    result = None

                if result is not None and result.face_landmarks:
                    landmarks = result.face_landmarks[0]
                    
                    if not self._face_present:
                        self._face_lock_start_t = now
                    self._face_present = True
                    face_secs += dt

                    # 1. Blink Rate (EAR) with 2-frame minimum and hysteresis (Item 7 & 8)
                    try:
                        ear_l = np.hypot(landmarks[159].x - landmarks[145].x, landmarks[159].y - landmarks[145].y) /                                 max(1e-4, np.hypot(landmarks[133].x - landmarks[33].x, landmarks[133].y - landmarks[33].y))
                        ear_r = np.hypot(landmarks[386].x - landmarks[374].x, landmarks[386].y - landmarks[374].y) /                                 max(1e-4, np.hypot(landmarks[362].x - landmarks[263].x, landmarks[362].y - landmarks[263].y))
                        ear = float((ear_l + ear_r) / 2.0)
                        self._current_ear = ear

                        # Eyes-open calibration collection
                        if getattr(self, '_ear_calibrating', False):
                            self._ear_calib_samples.append(ear)

                        c_thresh = getattr(self, '_ear_close_thresh', 0.19)
                        o_thresh = getattr(self, '_ear_reopen_thresh', 0.23)

                        if ear < c_thresh:
                            consecutive_closed += 1
                            if consecutive_closed >= 2 and not blink_closed:
                                blink_closed = True
                                recent_blinks.append(face_secs)
                                self._session_blinks += 1
                        elif ear > o_thresh:
                            consecutive_closed = 0
                            blink_closed = False

                        while recent_blinks and (face_secs - recent_blinks[0] > BPM_WINDOW):
                            recent_blinks.popleft()
                            
                        # Item 8: Show BPM only after 30 seconds of face time, averaged over 60s
                        if face_secs >= BPM_MIN_WINDOW:
                            window = min(BPM_WINDOW, face_secs)
                            self._current_bpm = (len(recent_blinks) / window * 60.0)
                        else:
                            self._current_bpm = None
                    except (IndexError, ZeroDivisionError, AttributeError, ValueError) as err:
                        self._last_blink_err = str(err)

                    # 2. Proximity & Turtle Neck (Z-Axis)
                    try:
                        # Landmarks 33 and 263 are the OUTER corners of the eyes.
                        # Real-world reference eye-width (default 9.0 cm, or user calibrated)
                        eye_dist_px = np.hypot(landmarks[33].x - landmarks[263].x, landmarks[33].y - landmarks[263].y) * frame.shape[1]
                        
                        # Standard webcam focal length approximation (fx ~ width * 0.85)
                        focal_approx = frame.shape[1] * 0.85
                        ref_w = getattr(self, '_eye_width_cm', 9.0)
                        raw_dist_cm = float(np.clip((ref_w * focal_approx) / max(1.0, eye_dist_px), 25.0, 110.0))
                        
                        # Add a smoothing filter so the distance doesn't jitter wildly while you breathe/move
                        if smooth_dist is None: smooth_dist = raw_dist_cm
                        smooth_dist += (raw_dist_cm - smooth_dist) * 0.15
                        
                        self._current_dist_cm = smooth_dist
                        self._turtle_neck = smooth_dist < 46.0
                        
                        # Lateral head tilt / posture lean
                        eye_dy = landmarks[263].y - landmarks[33].y
                        eye_dx = landmarks[263].x - landmarks[33].x
                        self._current_tilt_deg = float(np.degrees(np.arctan2(eye_dy, eye_dx)))
                    except (IndexError, ZeroDivisionError, AttributeError, ValueError) as err:
                        self._last_dist_err = str(err)

                    # 3. Emergency Brake (Mouth Open)
                    v_dist = np.hypot(landmarks[13].x - landmarks[14].x, landmarks[13].y - landmarks[14].y)
                    h_dist = np.hypot(landmarks[78].x - landmarks[308].x, landmarks[78].y - landmarks[308].y)
                    mar = v_dist / h_dist if h_dist > 0 else 0
                    
                    if mar > self._mouth_thresh: 
                        self._is_mouth_open = True
                        if not is_mouth_open:
                            is_mouth_open = True
                            mouth_open_start = now
                        elif not mouth_cooldown:
                            if now - mouth_open_start >= 1.0:
                                mouth_cooldown = True
                                current_state = self._mouse_on
                                self._post_ui(("set_mouse", not current_state))
                                
                                status_txt = "Tracking Resumed" if not current_state else "Emergency Paused"
                                self._ts_status(status_txt, color=ACCENT_AMBER)
                                self._ts_flash()
                    else:
                        self._is_mouth_open = False
                        is_mouth_open = False
                        if mar < 0.2: 
                            mouth_cooldown = False

                    # 4. Head Tracking & Smoothing
                    nose = landmarks[1]
                    self._raw_nose_x = float(nose.x)
                    self._raw_nose_y = float(nose.y)
                    self._norm_head_x = float(nose.x)
                    self._norm_head_y = float(nose.y)

                    nx = getattr(self, '_neutral_x', 0.5)
                    ny = getattr(self, '_neutral_y', 0.5)
                    self._nose_centered = bool(abs(nose.x - nx) <= 0.08 and abs(nose.y - ny) <= 0.08)
                    s_val = self._sensitivity
                    
                    x_range = [nx - s_val, nx + s_val]
                    y_range = [ny - s_val, ny + s_val]
                    
                    target_x = np.interp(nose.x, x_range, [0, screen_w])
                    target_y = np.interp(nose.y, y_range, [0, screen_h])
                    
                    distance = np.hypot(target_x - smoothed_x, target_y - smoothed_y)
                    dynamic_alpha = self._smoothing if distance > 40 else 0.15
                    
                    smoothed_x += dynamic_alpha * (target_x - smoothed_x)
                    smoothed_y += dynamic_alpha * (target_y - smoothed_y)
                    self._cursor_proj_x = int(smoothed_x)
                    self._cursor_proj_y = int(smoothed_y)

                    # Item 11: Real tremor steadiness measured in pixels of displacement variance
                    self._nose_history.append((smoothed_x, smoothed_y))
                    if len(self._nose_history) >= 6:
                        xs = [p[0] for p in self._nose_history]
                        ys = [p[1] for p in self._nose_history]
                        self._jitter_px = float(math.sqrt(np.var(xs) + np.var(ys)))
                    
                    if self._mouse_on:
                        try: pyautogui.moveTo(int(smoothed_x), int(smoothed_y), _pause=False)
                        except: pass

                        mode = self._mode_name
                        is_scrolling = False
                        
                        dock_w = 680
                        dock_h = 120 
                        dock_x = int((screen_w - dock_w) * self._dock_pos_x)
                        is_hovering_dock = (dock_x <= smoothed_x <= dock_x + dock_w) and (0 <= smoothed_y <= dock_h)

                        # 5. Smart Zone Scroll Logic
                        if mode == "Scroll" and not is_hovering_dock:
                            neutral_top = screen_h * 0.35
                            neutral_bottom = screen_h * 0.65
                            
                            if smoothed_y < neutral_top:
                                if now - last_scroll_time > 0.15: 
                                    try: pyautogui.scroll(int(self._scroll_speed)) 
                                    except: pass 
                                    last_scroll_time = now
                                self._ts_status("Scrolling Up...", color=ACCENT_CYAN)
                                is_scrolling = True
                            elif smoothed_y > neutral_bottom:
                                if now - last_scroll_time > 0.15:
                                    try: pyautogui.scroll(int(-self._scroll_speed))
                                    except: pass 
                                    last_scroll_time = now
                                self._ts_status("Scrolling Down...", color=ACCENT_CYAN)
                                is_scrolling = True
                            else:
                                self._ts_status("Neutral Zone (No Scroll)", color=TEXT_MUTED)

                        # 6. Action Logic (Click / Drag / Dwell)
                        if is_scrolling:
                            dwell_start_time = now
                            dwell_state = 0
                        else:
                            dwell_distance = np.hypot(smoothed_x - dwell_x, smoothed_y - dwell_y)
                            active_dwell_rad = getattr(self, '_dwell_radius', 25)
                            active_dwell_time = getattr(self, '_dwell_time', 1.0)
                            
                            if dwell_distance > active_dwell_rad:
                                dwell_x, dwell_y = smoothed_x, smoothed_y
                                dwell_start_time = now
                                if dwell_state != 0:
                                    if self._is_dragging:
                                        self._ts_status("Holding... Dwell to Drop!", color=ACCENT_AMBER)
                                    elif mode == "Scroll" and not is_hovering_dock:
                                        self._ts_status("Neutral Zone (No Scroll)", color=TEXT_MUTED)
                                    elif mode == "Type":
                                        self._ts_status("Type Mode: Dwell on keys", color=ACCENT_CYAN)
                                    else:
                                        self._ts_status("Moving...", color=TEXT_MUTED)
                                dwell_state = 0
                            else:
                                dwell_duration = now - dwell_start_time
                                if dwell_duration >= active_dwell_time and dwell_state == 0:
                                    self._total_clicks += 1
                                    self._lifetime_clicks += 1
                                    if mode == "Scroll":
                                        if is_hovering_dock:
                                            pyautogui.click(button='left')
                                            self._ts_status("Dock Clicked!", color=ACCENT_GREEN)
                                            self._ts_flash(color=ACCENT_GREEN)
                                        else:
                                            self._ts_status("Clicks Blocked (Scroll Mode)", color=TEXT_MUTED)
                                            
                                    elif mode == "Left" or mode == "Type":
                                        pyautogui.click(button='left')
                                        txt = "Left Click!" if mode == "Left" else "Key Pressed!"
                                        self._ts_status(txt, color=ACCENT_GREEN)
                                        self._ts_flash(color=ACCENT_GREEN)
                                    elif mode == "Right":
                                        pyautogui.click(button='right')
                                        self._ts_status("Right Click!", color=ACCENT_AMBER)
                                        self._ts_flash(color=ACCENT_AMBER)
                                        self._post_ui(("mode_left",))
                                    elif mode == "Double":
                                        pyautogui.doubleClick()
                                        self._ts_status("Double Click!", color=ACCENT_CYAN)
                                        self._ts_flash(color=ACCENT_CYAN)
                                        self._post_ui(("mode_left",))
                                    elif mode == "Drag":
                                        if not self._is_dragging:
                                            pyautogui.mouseDown()
                                            self._is_dragging = True
                                            self._ts_status("Holding... Dwell to Drop!", color=ACCENT_AMBER)
                                            self._ts_flash(color=ACCENT_AMBER)
                                        else:
                                            pyautogui.mouseUp()
                                            self._is_dragging = False
                                            self._ts_status("Dropped!", color=ACCENT_GREEN)
                                            self._ts_flash(color=ACCENT_GREEN)
                                            self._post_ui(("mode_left",))
                                        
                                    dwell_state = 1
                                    
                                elif dwell_state == 0 and dwell_duration > 0.15:
                                    countdown = max(0.0, active_dwell_time - dwell_duration)
                                    if mode == "Scroll":
                                        if is_hovering_dock:
                                            self._ts_status(f"Change Mode in {countdown:.1f}s", color=ACCENT_AMBER)
                                        else:
                                            self._ts_status("Clicks Blocked (Scroll Mode)", color=TEXT_MUTED)
                                    elif mode == "Drag" and self._is_dragging:
                                        self._ts_status(f"Drop in {countdown:.1f}s", color=ACCENT_AMBER)
                                    elif mode == "Type":
                                        self._ts_status(f"Press Key in {countdown:.1f}s", color=ACCENT_AMBER)
                                    else:
                                        self._ts_status(f"Click in {countdown:.1f}s", color=ACCENT_AMBER)

                    # 7. Draw Visualizers on Frame
                    preview_x = int(np.interp(nose.x, x_range, [0, frame.shape[1]]))
                    preview_y = int(np.interp(nose.y, y_range, [0, frame.shape[0]]))
                    
                    cv2.circle(rgb, (preview_x, preview_y), 7, (56, 189, 248), -1)
                    cv2.circle(rgb, (preview_x, preview_y), 14, (255, 255, 255), 1)
                    
                    if self._mouse_on and dwell_state == 0 and (now - dwell_start_time) > 0.15 and not is_scrolling:
                        if mode != "Scroll" or is_hovering_dock:
                            progress = min(1.0, (now - dwell_start_time) / max(0.1, active_dwell_time))
                            radius = int(36 * (1.0 - progress))
                            if radius > 4:
                                cv2.circle(rgb, (preview_x, preview_y), radius, (16, 185, 129), 2)
                            
                    if is_mouth_open and not mouth_cooldown:
                        mouth_progress = min(1.0, (now - mouth_open_start) / 1.0)
                        mouth_x = int(np.interp(landmarks[13].x, x_range, [0, frame.shape[1]]))
                        mouth_y = int(np.interp(landmarks[13].y, y_range, [0, frame.shape[0]]))
                        cv2.circle(rgb, (mouth_x, mouth_y), int(22 * mouth_progress), (244, 63, 94), -1)

                else:
                    # Face lost: drop stale readings so the UI shows "no face", not old numbers.
                    self._face_present = False
                    self._face_lock_start_t = None
                    self._current_dist_cm = None
                    self._turtle_neck = False
                    self._current_bpm = None
                    self._current_ear = None
                    self._is_mouth_open = False
                    self._nose_centered = False
                    smooth_dist = None
                    blink_closed = False
                    consecutive_closed = 0

                # Item 1: Resize in camera thread, not the UI thread
                target_w = getattr(self, '_cam_preview_w', 320)
                target_h = getattr(self, '_cam_preview_h', 240)
                if target_w > 10 and target_h > 10:
                    rf_h, rf_w = rgb.shape[:2]
                    scale = min(target_w / rf_w, target_h / rf_h)
                    disp_w, disp_h = max(10, int(rf_w * scale)), max(10, int(rf_h * scale))
                    preview_frame = cv2.resize(rgb, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
                else:
                    preview_frame = rgb

                # Put newest frame, dropping oldest if UI hasn't drawn it yet
                try:
                    if self._frame_queue.full():
                        try:
                            self._frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                    self._frame_queue.put_nowait((preview_frame, rgb))
                except Exception:
                    pass
                
                # Item 3: Cap camera thread at ~30 fps using time.sleep(max(0, 1/30 - elapsed))
                elapsed = time.monotonic() - loop_start
                time.sleep(max(0.0, (1.0 / 30.0) - elapsed))
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass
        self._active_cap = None

    def _poll_frame_queue(self):
        """Item 1: Poll every ~33 ms, skip unrendered frames, reuse CTkImage, resized in camera thread."""
        try:
            self._drain_ui_events()

            # Item 4: Stop video and widget updates while Profile or Motor is scrolling
            if ("Profile" in getattr(self, '_current_tab', '') or "Motor" in getattr(self, '_current_tab', '')) and (
                time.monotonic() - getattr(self, '_last_scroll_time', 0.0) < 0.35
            ):
                return

            latest_item = None
            while not self._frame_queue.empty():
                try:
                    latest_item = self._frame_queue.get_nowait()
                except queue.Empty:
                    break

            if latest_item is not None:
                preview_frame, full_rgb = latest_item
                if not self._camera_live:
                    try:
                        if hasattr(self, '_placeholder') and self._placeholder is not None:
                            self._placeholder.destroy()
                    except Exception:
                        pass
                    self.video_label.place(relx=0.5, rely=0.5, anchor="center")
                    self._camera_live = True

                # Forward full frame to Always-on-Top Floating Face Cam if active
                if getattr(self, "_floating_face_cam", None) is not None:
                    try:
                        if self._floating_face_cam.winfo_exists():
                            self._floating_face_cam.update_frame(full_rgb)
                        else:
                            self._floating_face_cam = None
                            if hasattr(self, "_floating_cam_var"):
                                self._floating_cam_var.set(False)
                    except Exception:
                        self._floating_face_cam = None

                # Update desired UI width/height for the camera thread
                try:
                    ui_w = self.camera_frame.winfo_width()
                    ui_h = self.camera_frame.winfo_height()
                    if ui_w > 10 and ui_h > 10:
                        self._cam_preview_w = ui_w
                        self._cam_preview_h = ui_h
                except Exception:
                    pass

                fh, fw = preview_frame.shape[:2]
                img = Image.fromarray(preview_frame)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(fw, fh))
                self._video_ctk_image = ctk_img
                self.video_label.configure(image=ctk_img)
                if not self.video_label.winfo_ismapped() and "Cockpit" in getattr(self, '_current_tab', ''):
                    self.video_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            pass
        finally:
            # Poll every ~33 ms (~30 FPS) - Guaranteed reschedule
            if getattr(self, '_cam_running', True):
                self.after(33, self._poll_frame_queue)

    def _start_wellness_sync(self):
        """Item 2: Run _sync_wellness_ui ~5 times a second (every 200 ms)."""
        try:
            self._sync_wellness_ui()
        except Exception:
            pass
        finally:
            if getattr(self, '_cam_running', True):
                self.after(200, self._start_wellness_sync)

    def _set_label(self, widget, text, color=None):
        """configure() a label only if its text/colour actually changed (avoids 60 Hz redraws)."""
        key = (text, color)
        if getattr(widget, "_v360_last", None) == key:
            return
        widget._v360_last = key
        if color is None:
            widget.configure(text=text)
        else:
            widget.configure(text=text, text_color=color)

    def _sync_wellness_ui(self):
        """Synchronize telemetry displays, biometric gauges and HUD strip (main thread only)."""
        bpm = self._current_bpm          # None while measuring
        dist = self._current_dist_cm     # None when no face is on camera

        # ── Posture uptime: time-based, accumulates regardless of which tab is open ──
        now = time.monotonic()
        dt = min(0.5, now - self._last_sync_t) if self._last_sync_t is not None else 0.0
        self._last_sync_t = now
        if dist is not None:
            self._posture_total_secs += dt
            if dist >= 50.0:             # 50 cm+ counts as healthy upright posture
                self._posture_good_secs += dt
        uptime_pct = (int(self._posture_good_secs / self._posture_total_secs * 100)
                      if self._posture_total_secs >= 5.0 else None)

        # ── Blink status ──
        if bpm is None:
            bpm_color, bpm_status, bpm_num = TEXT_MUTED, "Measuring", "--"
        else:
            bpm_num = f"{int(round(bpm))}"
            if bpm >= 14:
                bpm_color, bpm_status = ACCENT_GREEN, "Healthy"
            elif bpm >= 10:
                bpm_color, bpm_status = ACCENT_AMBER, "Moderate"
            else:
                bpm_color, bpm_status = ACCENT_RED, "Visual Fatigue"

        # ── Posture status + adaptive global alert ──
        alert_needed = False
        is_critical = False
        if dist is None:
            posture_color = TEXT_MUTED
            posture_txt = "Posture: -- (No face detected)"
        elif dist < 46.0:
            posture_color = ACCENT_RED
            posture_txt = f"⚠️ Posture: {int(dist)} cm (Turtle Neck Alert)"
            alert_needed = True
            is_critical = True
        elif dist < 52.0:
            posture_color = ACCENT_AMBER
            posture_txt = f"Posture: {int(dist)} cm (Leaning In)"
            alert_needed = True
        else:
            posture_color = ACCENT_GREEN
            posture_txt = f"Posture: {int(dist)} cm (Optimal)"

        if alert_needed:
            if not hasattr(self, 'global_alert') or not self.global_alert.winfo_exists():
                self.global_alert = GlobalPostureAlert(self, dist, is_critical)
            else:
                self.global_alert.update_dist(dist, is_critical)
        else:
            if hasattr(self, 'global_alert') and self.global_alert.winfo_exists():
                self.global_alert.destroy()

        # Item 2: Update persistent header + bottom HUD about twice a second (every 500 ms)
        lat = self._latency_ms
        if now - getattr(self, '_last_hud_sync_t', 0.0) >= 0.5:
            self._last_hud_sync_t = now
            if lat is None:
                lat_txt, lat_col = "● Latency: --", TEXT_MUTED
            else:
                lat_txt = f"● {lat:.0f} ms Latency"
                lat_col = ACCENT_GREEN if lat < 50 else (ACCENT_AMBER if lat < 100 else ACCENT_RED)
            self._set_label(self.latency_badge, lat_txt, lat_col)
            self._set_label(self.hud_blink_txt, f"Blink Rate: {bpm_num} BPM ({bpm_status})", bpm_color)
            self._set_label(self.hud_posture_txt, posture_txt, posture_color)

        # ── Cockpit dashboard telemetry sync (only while that tab is visible) ──
        if "Cockpit" in self._current_tab:
            lum = getattr(self, '_ambient_lum', None)
            pct = getattr(self, '_ambient_brightness_pct', None)
            if lum is None or pct is None:
                if hasattr(self, 'lux_val_lbl'):
                    self._set_label(self.lux_val_lbl, "Scene Brightness: --%", TEXT_MUTED)
                if hasattr(self, 'lux_status_lbl'):
                    self._set_label(self.lux_status_lbl, "📷 Measuring Scene Illumination...", TEXT_MUTED)
                if hasattr(self, 'lux_tip_lbl'):
                    self._set_label(self.lux_tip_lbl, "Photometric sensor analyzes webcam scene luminance.")
                if hasattr(self, 'lux_bar'):
                    self.lux_bar.set(0.0)
            else:
                if hasattr(self, 'lux_bar'):
                    self.lux_bar.set(lum)
                if lum < 0.22:
                    l_col = ACCENT_AMBER if lum >= 0.14 else ACCENT_RED
                    l_stat = "⚠️ Low Light (Eye Strain Risk)"
                    l_tip = "Dim room lighting increases eye strain and sensor noise."
                elif lum > 0.82:
                    l_col = ACCENT_AMBER
                    l_stat = "⚠️ Harsh Glare / Overexposed"
                    l_tip = "Harsh glare causes screen contrast fatigue. Soften lights."
                else:
                    l_col = ACCENT_GREEN
                    l_stat = "🟢 Optimal Ergonomic Illumination"
                    l_tip = "Balanced room lighting minimizes eye fatigue and sensor noise."
                # Item 11: Replace Lux with Scene Brightness %
                if hasattr(self, 'lux_val_lbl'):
                    self._set_label(self.lux_val_lbl, f"Scene Brightness: {pct}%", l_col)
                if hasattr(self, 'lux_status_lbl'):
                    self._set_label(self.lux_status_lbl, l_stat, l_col)
                if hasattr(self, 'lux_tip_lbl'):
                    self._set_label(self.lux_tip_lbl, l_tip)
                if hasattr(self, 'lux_bar'):
                    self.lux_bar.configure(progress_color=l_col)

            # Item 11: Real numbers in Cockpit (Locked · mm:ss, real FPS and real latency)
            if hasattr(self, 'cockpit_face_lbl'):
                if self._face_present:
                    lock_t = getattr(self, '_face_lock_start_t', None)
                    if lock_t is not None:
                        sec_locked = int(now - lock_t)
                        mm, ss = divmod(sec_locked, 60)
                        self._set_label(self.cockpit_face_lbl, f"Locked · {mm:02d}:{ss:02d}", ACCENT_GREEN)
                    else:
                        self._set_label(self.cockpit_face_lbl, "Locked · 00:00", ACCENT_GREEN)
                else:
                    self._set_label(self.cockpit_face_lbl, "Searching...", TEXT_MUTED)
            if hasattr(self, 'cockpit_speed_lbl'):
                cur_lat = int(round(lat)) if lat is not None else 0
                real_fps = int(round(getattr(self, '_real_fps', 30.0)))
                self._set_label(self.cockpit_speed_lbl, f"{real_fps} FPS · {cur_lat}ms", ACCENT_CYAN)
            if hasattr(self, 'cockpit_reticle_lbl'):
                if not self._face_present:
                    self._set_label(self.cockpit_reticle_lbl, "Standby", TEXT_MUTED)
                elif getattr(self, '_nose_centered', True):
                    self._set_label(self.cockpit_reticle_lbl, "Centered (Lock)", ACCENT_GREEN)
                else:
                    self._set_label(self.cockpit_reticle_lbl, "Off-Center", ACCENT_AMBER)
            if hasattr(self, 'cockpit_mouth_lbl'):
                if getattr(self, '_is_mouth_open', False):
                    self._set_label(self.cockpit_mouth_lbl, "Paused (Open)", ACCENT_RED)
                else:
                    self._set_label(self.cockpit_mouth_lbl, "Ready (Closed)", ACCENT_CYAN)
            if hasattr(self, 'cockpit_dist_lbl'):
                if dist is not None:
                    d_txt = f"{int(dist)} cm (Optimal)" if dist >= 50 else f"{int(dist)} cm (Turtle Neck)"
                    d_col = ACCENT_GREEN if dist >= 50 else ACCENT_RED
                    self._set_label(self.cockpit_dist_lbl, d_txt, d_col)
                else:
                    self._set_label(self.cockpit_dist_lbl, "No Face", TEXT_MUTED)
            if hasattr(self, 'cockpit_bpm_lbl'):
                self._set_label(self.cockpit_bpm_lbl, f"{bpm_num} BPM ({bpm_status})", bpm_color)

        # ── Motor dashboard widgets (only while that tab is visible) ──
        if "Motor" in self._current_tab:
            if hasattr(self, 'scroll_radar'):
                self.scroll_radar.set_altitude(getattr(self, '_norm_head_y', 0.5))
            if hasattr(self, 'motor_coords_lbl'):
                cx = getattr(self, '_cursor_proj_x', 0)
                cy = getattr(self, '_cursor_proj_y', 0)
                self._set_label(self.motor_coords_lbl, f"X: {cx} px  |  Y: {cy} px")
            if hasattr(self, 'motor_stab_lbl'):
                # Item 11: Measure steadiness in pixels of displacement jitter
                jitter = getattr(self, '_jitter_px', 2.1)
                if jitter <= 4.0:
                    stab_status, stab_col = "Steady", ACCENT_GREEN
                elif jitter <= 10.0:
                    stab_status, stab_col = "Mild Jitter", ACCENT_AMBER
                else:
                    stab_status, stab_col = "Tremor", ACCENT_RED
                self._set_label(self.motor_stab_lbl, f"±{jitter:.1f} px ({stab_status})", stab_col)

        # ── EyeGym live gaze tracking & telemetry (only while that tab is visible) ──
        if "EyeGym" in self._current_tab:
            if hasattr(self, 'dedicated_gym_canvas'):
                nx = getattr(self, '_norm_head_x', 0.5)
                ny = getattr(self, '_norm_head_y', 0.5)
                self.dedicated_gym_canvas.update_gaze_pos(nx, ny)
                acc = self.dedicated_gym_canvas.accuracy
                laps = self.dedicated_gym_canvas.laps_done
                locked = self.dedicated_gym_canvas.locked
                if hasattr(self, 'gym_sync_lbl'):
                    stat_txt = f"{acc:.1f}% (Optimal)" if locked else f"{acc:.1f}% (Seeking)"
                    stat_col = ACCENT_GREEN if locked else ACCENT_AMBER
                    self._set_label(self.gym_sync_lbl, stat_txt, stat_col)
                if hasattr(self, 'gym_laps_lbl'):
                    self._set_label(self.gym_laps_lbl, f"{laps} / 10 Laps")
                if hasattr(self, 'gym_lap_progress_lbl'):
                    self._set_label(self.gym_lap_progress_lbl, f"Workout Progress: {laps % 10} / 10 Laps (+50 XP Bonus)")
                if hasattr(self, 'gym_lap_bar'):
                    self.gym_lap_bar.set(min(1.0, (laps % 10) / 10.0))

        # ── EyeRest dashboard widgets (only while that tab is visible) ──
        if "EyeRest" not in self._current_tab:
            return

        # Item 7: Live EAR readout
        if hasattr(self, 'live_ear_lbl'):
            cur_ear = getattr(self, '_current_ear', None)
            c_th = getattr(self, '_ear_close_thresh', 0.19)
            if cur_ear is not None:
                self.live_ear_lbl.configure(text=f"EAR: {cur_ear:.2f} (Thresh: {c_th:.2f})")
            else:
                self.live_ear_lbl.configure(text=f"EAR: -- (Thresh: {c_th:.2f})")

        self.posture_canvas.set_posture(dist, getattr(self, '_current_tilt_deg', 0.0))
        self.blink_freq_gauge.set_value(bpm, bpm_status)

        total_sec = self._break_interval_mins * 60.0
        elapsed_mins = int((time.time() - self._session_start) / 60)
        self.rule_2020_gauge.set_timer(self._cycle_20_20, total_sec, elapsed_mins=elapsed_mins)
        rem_m, rem_s = divmod(int(self._cycle_20_20), 60)
        self._set_label(self.cycle_timer_lbl, f"Next Break in: {rem_m:02d}m {rem_s:02d}s")
        self._set_label(self.away_gaze_lbl, f"Away-Gaze Cycles: {self._away_gazes_done} Completed")
        self._set_label(self.blink_rate_lbl, f"Blink Rate: {bpm_num}/min")

        rings = (
            round(min(1.0, bpm / 18.0), 2) if bpm is not None else 0.0,
            round(min(1.0, self._away_gazes_done / 8.0), 2),
            round(uptime_pct / 100.0, 2) if uptime_pct is not None else 0.0,
        )
        if rings != self._last_rings:
            self._last_rings = rings
            self.rings_canvas.set_metrics(*rings)

        # ── Session analytics grid ──
        if uptime_pct is None:
            p_text, p_col = "-- (Measuring)", TEXT_MUTED
        elif uptime_pct >= 80:
            p_text, p_col = f"{uptime_pct}% (Good)", ACCENT_CYAN
        elif uptime_pct >= 50:
            p_text, p_col = f"{uptime_pct}% (Fair)", ACCENT_AMBER
        else:
            p_text, p_col = f"{uptime_pct}% (Poor)", ACCENT_RED
        self._set_label(self.stat_posture_lbl, p_text, p_col)

        self._set_label(self.stat_blink_lbl, f"{bpm_num} BPM ({bpm_status})" if bpm is not None else "-- (Measuring)", bpm_color)
        self._set_label(self.stat_breaks_lbl, f"{self._away_gazes_done} / 8 Cycles")

        if bpm is None or uptime_pct is None:
            f_text, f_col = "-- (Measuring)", TEXT_MUTED
        elif bpm < 10 or uptime_pct < 50 or (dist is not None and dist < 46.0):
            f_text, f_col = "High (🔴 Risk)", ACCENT_RED
        elif bpm < 14 or uptime_pct < 80 or (dist is not None and dist < 52.0):
            f_text, f_col = "Moderate (🟡 Watch)", ACCENT_AMBER
        else:
            f_text, f_col = "Low (🟢 Safe)", ACCENT_GREEN
        self._set_label(self.stat_fatigue_lbl, f_text, f_col)

        if uptime_pct is None:
            self._set_label(self.relief_badge, "Fatigue Relief Index: --", TEXT_MUTED)
        else:
            r_col = ACCENT_GREEN if uptime_pct >= 80 else (ACCENT_AMBER if uptime_pct >= 50 else ACCENT_RED)
            self._set_label(self.relief_badge, f"Fatigue Relief Index: {uptime_pct}%", r_col)

if __name__ == "__main__":
    app = Vision360App()
    app.mainloop()
    app._cam_running = False