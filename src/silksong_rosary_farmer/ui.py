import sys
import threading
import time
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk, ImageSequence
from pynput.keyboard import Key, Listener

from silksong_rosary_farmer.farm import farm
from silksong_rosary_farmer.monitor import list_monitors


dir_images = Path(__file__).parent.parent.parent / "static"


class RosaryAutoFarmer(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # --- app/taskbar icon setup ---
        # Windows: set explicit AppUserModelID so taskbar uses *your* icon/group
        if sys.platform.startswith("win"):
            try:
                import ctypes

                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "com.rosary.autofarmer"  # any stable string
                )
            except Exception:
                pass
        ico_path = dir_images / "icon.ico"
        png_path = dir_images / "icon.png"  # fallback for other platforms
        # Prefer .ico on Windows (affects title bar + taskbar)
        if ico_path.exists():
            try:
                self.iconbitmap(default=str(ico_path))
            except Exception:
                pass
        # Fallback/use on Linux/macOS window chrome (PNG via PhotoImage)
        try:
            if png_path.exists():
                _icon_img = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, _icon_img)
        except Exception:
            pass
        # --- end app/taskbar icon setup ---

        self.title("Rosary Autofarmer")
        self.geometry("600x700")
        self.minsize(600, 700)

        # state
        self.running = False
        self.start_time = 0.0
        self.timer_var = ctk.StringVar(value="00:00:00")
        self.farm_thread = None
        self.stop_event = threading.Event()
        self.esc_listener = None

        # layout: one column, log grows
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # header with icons and title
        img_path = dir_images / "Rosary_Necklace.png"
        img = Image.open(img_path)
        self.rosary_img = ctk.CTkImage(
            light_image=img, dark_image=img, size=(132 / 2, 116 / 2)
        )

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=16, pady=(30, 80), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        header.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(header, text="", image=self.rosary_img).grid(
            row=0, column=0, sticky="e"
        )
        ctk.CTkLabel(
            header,
            text="ROSARY AUTOFARMER",
            font=ctk.CTkFont(size=36, weight="bold"),
        ).grid(row=0, column=1, padx=16, sticky="n")
        ctk.CTkLabel(header, text="", image=self.rosary_img).grid(
            row=0, column=2, sticky="w"
        )

        # start section (animated GIF above the button)
        start_wrap = ctk.CTkFrame(self, fg_color="transparent")
        start_wrap.grid(row=1, column=0, padx=16, pady=10, sticky="n")

        self.hornet_label = ctk.CTkLabel(start_wrap, text="")
        self.hornet_label.grid(row=0, column=0, pady=(0, 8), sticky="n")

        self.start_btn = ctk.CTkButton(
            start_wrap,
            text="START",
            width=260,
            height=90,
            font=ctk.CTkFont(size=22, weight="bold"),
            command=self.toggle_timer,
            fg_color="#993831",
            hover_color="#7f2f29",
            text_color="#ffffff",
        )
        self.start_btn.grid(row=1, column=0, sticky="n")

        # start GIF animation
        self._init_hornet_gif()

        # controls row (borderless)
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=2, column=0, padx=16, pady=6, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(3, weight=1)

        monitor_names = [name for name, _ in list_monitors()]
        self.monitor_combo = ctk.CTkComboBox(
            controls,
            values=monitor_names,
            state="readonly",
            width=260,
            font=ctk.CTkFont(size=22),
            command=self.on_monitor_change,
        )
        self.monitor_combo.set(monitor_names[0])
        self.monitor_combo.grid(row=0, column=1, padx=(0, 8))

        # timer (simple card, no border)
        timer_box = ctk.CTkFrame(controls, fg_color=("#2b2b2b", "#2b2b2b"))
        timer_box.grid(row=0, column=2, padx=(8, 0))
        ctk.CTkLabel(
            timer_box,
            textvariable=self.timer_var,
            font=ctk.CTkFont(size=22, weight="bold"),
            padx=18,
            pady=10,
        ).pack()

        # scrollable log
        log_wrap = ctk.CTkFrame(self, fg_color="transparent")
        log_wrap.grid(row=3, column=0, padx=16, pady=(6, 16), sticky="nsew")
        log_wrap.grid_rowconfigure(0, weight=1)
        log_wrap.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_wrap,
            wrap="word",
            activate_scrollbars=False,
            font=ctk.CTkFont(size=18),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        vscroll = ctk.CTkScrollbar(log_wrap, command=self.log_text.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=vscroll.set)

        self.log("Press START to start farming")
        self.log("You can press 'esc' to quickly stop, or just press the button again")
        self.bind("<Return>", lambda _e: self.toggle_timer())

    # window -> content size
    def fit_to_content(self):
        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}")

    # timer logic
    def toggle_timer(self):
        if not self.running:
            self.running = True
            self.start_time = time.monotonic()
            self.start_btn.configure(text="STOP")
            self.log("Go!")
            self._tick()
            self.start_farming()
        else:
            self.stop_farming()

    def start_farming(self):
        """Start the farm function in a separate thread"""
        # Clear the stop event
        self.stop_event.clear()

        # Get the selected monitor index
        monitor_names = [name for name, _ in list_monitors()]
        selected_monitor = self.monitor_combo.get()
        monitor_index = monitor_names.index(selected_monitor)

        self.log("Waiting 10 seconds...")
        time.sleep(10)

        # Start the global ESC listener
        self._start_esc_listener()

        # Start the farm thread
        self.farm_thread = threading.Thread(
            target=farm,
            args=(monitor_index,),
            kwargs={"stop_event": self.stop_event},
            daemon=True,
        )
        self.farm_thread.start()
        self.log(f"Started farming on {selected_monitor}")
        self.log("🎮 Press ESC to stop farming")

    def stop_farming(self):
        """Stop the farm thread"""
        if self.running:
            self.running = False
            self.start_btn.configure(text="START")
            self.log(f"Stopped at {self.timer_var.get()}")

            # Stop the global ESC listener
            self._stop_esc_listener()

            # Signal the farm thread to stop
            self.stop_event.set()

            if self.farm_thread and self.farm_thread.is_alive():
                self.log("Stopping farm thread...")
                # Give it a moment to clean up
                self.after(100, self._check_thread_stopped)

    def _tick(self):
        if not self.running:
            return
        elapsed = int(time.monotonic() - self.start_time)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self._tick)

    def _check_thread_stopped(self):
        """Check if the farm thread has stopped"""
        if self.farm_thread and self.farm_thread.is_alive():
            # Still running, check again in a bit
            self.after(100, self._check_thread_stopped)
        else:
            self.log("Farm thread stopped successfully")

    def _start_esc_listener(self):
        """Start a global keyboard listener for the ESC key"""

        def on_press(key):
            if key == Key.esc and self.running:
                print("\n🛑 ESC detected - stopping farm...")
                # Use after() to call stop_farming from the main thread
                self.after(0, self.stop_farming)

        self.esc_listener = Listener(on_press=on_press)
        self.esc_listener.start()

    def _stop_esc_listener(self):
        """Stop the global keyboard listener"""
        if self.esc_listener:
            try:
                self.esc_listener.stop()
                self.esc_listener = None
            except Exception:
                pass

    # helpers
    def on_monitor_change(self, choice: str):
        self.log(f"Monitor selected: {choice}")

    def log(self, msg: str):
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")

    def _init_hornet_gif(self):
        gif_path = dir_images / "hornet.gif"
        self._hornet_frames = []
        self._hornet_delays = []
        try:
            im = Image.open(gif_path)
            # scale frames to fit nicely above the button
            max_size = (260, 140)
            for frame in ImageSequence.Iterator(im):
                # duration per frame (ms), default 100 if missing
                delay = frame.info.get("duration", 100)
                self._hornet_delays.append(max(20, delay))

                fr = frame.convert("RGBA")
                fr.thumbnail(max_size, Image.Resampling.LANCZOS)
                self._hornet_frames.append(ImageTk.PhotoImage(fr))

            if self._hornet_frames:
                self._animate_hornet(0)
        except Exception:
            # silently ignore if GIF not available
            pass

    def _animate_hornet(self, idx=0):
        if not getattr(self, "_hornet_frames", None):
            return
        self.hornet_label.configure(image=self._hornet_frames[idx])
        next_idx = (idx + 1) % len(self._hornet_frames)
        delay = self._hornet_delays[idx] if self._hornet_delays else 100
        self.after(delay, lambda: self._animate_hornet(next_idx))


if __name__ == "__main__":
    app = RosaryAutoFarmer()
    app.mainloop()
