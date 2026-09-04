import os
import sys
import random
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# --- Fix 1: Try importing PIL to handle PNG files properly on Linux ---
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def setup_desktop_shortcut():
    """Automatically creates a proper Linux .desktop entry."""
    if not sys.platform.startswith("linux"):
        return

    script_path = os.path.abspath(__file__)
    working_dir = os.path.dirname(script_path)
    icon_path = os.path.join(working_dir, "icon.png")
    
    apps_dir = Path.home() / ".local" / "share" / "applications"
    shortcut_path = apps_dir / "workout-tracker.desktop"

    apps_dir.mkdir(parents=True, exist_ok=True)

    desktop_file_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Workout Tracker
Comment=Log and track your workouts
Exec=python3 "{script_path}"
Path={working_dir}
Icon={icon_path}
Terminal=false
StartupWMClass=workout-tracker
Categories=Utility;Sports;
"""

    try:
        shortcut_path.write_text(desktop_file_content)
        shortcut_path.chmod(0o755)
    except Exception as e:
        print(f"Could not create desktop shortcut: {e}")


class ConfettiCanvas(tk.Canvas):
    """Overlay canvas that renders falling confetti particles."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, bd=0, bg="#1e1e2e", **kwargs)
        self.particles = []

    def start_confetti(self, particle_count=70):
        """Spawns confetti particles centered near the top and starts animation."""
        self.delete("all")
        self.particles.clear()
        
        colors = ["#f38ba8", "#89b4fa", "#a6e3a1", "#f9e2af", "#cba6f7", "#fab387"]
        
        width = self.winfo_width() or 600
        center_x = width // 2

        for _ in range(particle_count):
            x = random.randint(center_x - 150, center_x + 150)
            y = random.randint(-80, -10)
            size = random.randint(6, 10)
            color = random.choice(colors)
            
            if random.random() > 0.5:
                p_id = self.create_rectangle(x, y, x + size, y + size, fill=color, outline="")
            else:
                p_id = self.create_oval(x, y, x + size, y + size, fill=color, outline="")

            speed_x = random.uniform(-3.5, 3.5)
            speed_y = random.uniform(3, 8)
            self.particles.append({"id": p_id, "speed_y": speed_y, "speed_x": speed_x})

        self._animate(frame=0)

    def _animate(self, frame):
        """Animates particles falling down."""
        height = self.winfo_height() or 680
        active_particles = False

        for p in self.particles:
            self.move(p["id"], p["speed_x"], p["speed_y"])
            coords = self.coords(p["id"])
            if coords and coords[1] < height:
                active_particles = True

        if active_particles and frame < 75:
            self.after(25, lambda: self._animate(frame + 1))
        else:
            self.delete("all")
            self.particles.clear()
            self.place_forget()


class RoundedFrame(tk.Canvas):
    """Custom Canvas container that draws a background card with rounded corners."""
    def __init__(self, parent, bg_color="#1e1e2e", card_color="#25263a", radius=20, **kwargs):
        super().__init__(parent, bg=bg_color, highlightthickness=0, bd=0, **kwargs)
        self.card_color = card_color
        self.radius = radius

        self.inner_frame = tk.Frame(self, bg=card_color)
        self.create_window((radius, radius), window=self.inner_frame, anchor="nw", tags="inner_window")

        self.bind("<Configure>", self._draw_rounded_card)

    def _draw_rounded_card(self, event):
        self.delete("card")
        w, h = event.width, event.height
        r = self.radius

        self.create_polygon(
            r, 0, w - r, 0,
            w, 0, w, r,
            w, h - r, w, h,
            w - r, h, r, h,
            0, h, 0, h - r,
            0, r, 0, 0,
            smooth=True,
            fill=self.card_color,
            tags="card"
        )
        self.tag_lower("card")
        self.itemconfig("inner_window", width=w - (r * 2), height=h - (r * 2))


class RoundedCheckbutton(tk.Canvas):
    """Custom rounded/circular checkbox built using Tkinter Canvas."""
    def __init__(self, parent, text, variable, on_toggle=None, bg_color="#25263a", fg_color="#cdd6f4", active_color="#89b4fa", **kwargs):
        super().__init__(parent, bg=bg_color, highlightthickness=0, bd=0, height=30, cursor="hand2", **kwargs)
        self.variable = variable
        self.text = text
        self.on_toggle = on_toggle
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.active_color = active_color

        self.hit_bg = self.create_rectangle(0, 0, 300, 30, fill=bg_color, outline="", tags="clickable")
        self.rect_id = self.create_oval(4, 5, 22, 23, outline="#45475a", width=2, fill="#1e1e2e", tags="clickable")
        self.check_id = self.create_oval(8, 9, 18, 19, fill=active_color, state="hidden", outline="", tags="clickable")
        self.text_id = self.create_text(30, 14, text=text, anchor="w", fill=fg_color, font=("Segoe UI", 11, "bold"), tags="clickable")

        self.tag_bind("clickable", "<Button-1>", self.toggle)
        self.update_state()

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())
        self.update_state()
        if self.on_toggle:
            self.on_toggle()

    def update_state(self):
        if self.variable.get():
            self.itemconfig(self.check_id, state="normal")
            self.itemconfig(self.rect_id, outline=self.active_color, fill="#25263a")
        else:
            self.itemconfig(self.check_id, state="hidden")
            self.itemconfig(self.rect_id, outline="#45475a", fill="#1e1e2e")


class ExerciseRow(tk.Frame):
    """Widget row for an exercise, including toggle and detail input fields."""
    def __init__(self, parent, name, category, variable, **kwargs):
        super().__init__(parent, bg="#25263a", **kwargs)
        self.name = name
        self.category = category
        self.variable = variable

        self.entries = {}

        self.cb = RoundedCheckbutton(self, text=name, variable=variable, on_toggle=self.toggle_inputs)
        self.cb.pack(fill="x", anchor="w")

        self.input_frame = tk.Frame(self, bg="#1e1e2e", padx=4, pady=6)

        if category == "strength":
            self._add_entry_field("sets", "Sets:", width=3)
            self._add_entry_field("reps", "Reps:", width=3)
            self._add_entry_field("weight", "Kg:", width=4)
        elif category == "cardio":
            self._add_entry_field("distance", "Km:", width=4)
            self._add_entry_field("time", "Min:", width=4)
        elif category == "stretch":
            self._add_entry_field("time", "Min:", width=4)

    def _add_entry_field(self, key, label_text, width):
        lbl = tk.Label(self.input_frame, text=label_text, font=("Segoe UI", 8, "bold"), bg="#1e1e2e", fg="#a6adc8")
        lbl.pack(side="left", padx=(2, 1))
        
        entry = tk.Entry(
            self.input_frame, 
            width=width, 
            bg="#25263a", 
            fg="#cdd6f4", 
            bd=0, 
            relief="flat", 
            insertbackground="#cdd6f4", 
            font=("Segoe UI", 9)
        )
        entry.pack(side="left", padx=(0, 4))
        self.entries[key] = entry

    def toggle_inputs(self):
        if self.variable.get() and (self.category in ["strength", "cardio", "stretch"]):
            self.input_frame.pack(fill="x", pady=(4, 0))
        else:
            self.input_frame.pack_forget()

    def get_details(self):
        if not self.variable.get():
            return None

        details = []
        if self.category == "strength":
            sets = self.entries.get("sets").get().strip()
            reps = self.entries.get("reps").get().strip()
            weight = self.entries.get("weight").get().strip()

            if sets: details.append(f"{sets} sets")
            if reps: details.append(f"{reps} reps")
            if weight: details.append(f"{weight}kg")
        elif self.category == "cardio":
            dist = self.entries.get("distance").get().strip()
            time = self.entries.get("time").get().strip()

            if dist: details.append(f"{dist}km")
            if time: details.append(f"{time}min")
        elif self.category == "stretch":
            time = self.entries.get("time").get().strip()
            if time: details.append(f"{time}min")

        if details:
            return f"{self.name} ({', '.join(details)})"
        return self.name

    def reset(self):
        self.variable.set(False)
        self.cb.update_state()
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.input_frame.pack_forget()


class WorkoutApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Workout Tracker")
        self.master.geometry("600x680")
        self.master.configure(bg="#1e1e2e")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_path = os.path.join(script_dir, "workout_log.txt")

        # --- Fix 2: Enhanced PNG Loading via Pillow ---
        icon_path = os.path.join(script_dir, "icon.png")
        if os.path.exists(icon_path):
            try:
                if HAS_PIL:
                    pil_img = Image.open(icon_path)
                    self.icon_img = ImageTk.PhotoImage(pil_img)
                else:
                    self.icon_img = tk.PhotoImage(file=icon_path)
                
                self.master.iconphoto(True, self.icon_img)
            except Exception as e:
                print(f"[Warning] Could not load icon.png: {e}")
        else:
            print(f"[Warning] icon.png not found in directory: {script_dir}")

        # Exercise Config
        self.exercise_config = [
            ("Chest - Bench press", "strength"),
            ("Chest - Dumbbells", "strength"),
            ("Legs - Leg press", "strength"),
            ("Legs - Squats", "strength"),
            ("Back - Chins", "strength"),
            ("Back - Dumbbells", "strength"),
            ("Biceps", "strength"),
            ("Triceps", "strength"),
            ("Running", "cardio"),
            ("Biking", "cardio"),
            ("Walking", "cardio"),
            ("Climbing", "strength"),
            ("Stretch", "stretch"),
            ("Yoga", "stretch")
        ]

        self.workouts = {item[0]: tk.BooleanVar(value=False) for item in self.exercise_config}
        self.exercise_widgets = []

        # Header
        header_frame = tk.Frame(self.master, bg="#1e1e2e")
        header_frame.pack(fill="x", padx=25, pady=(20, 10))

        title = tk.Label(
            header_frame, 
            text="WORKOUT LOG", 
            font=("Segoe UI", 18, "bold"), 
            bg="#1e1e2e", 
            fg="#cdd6f4"
        )
        title.pack(anchor="w")

        sub_frame = tk.Frame(header_frame, bg="#1e1e2e")
        sub_frame.pack(anchor="w")

        tk.Label(sub_frame, text="Select workouts and enter values. Use ", font=("Segoe UI", 9), bg="#1e1e2e", fg="#a6adc8").pack(side="left")
        tk.Label(sub_frame, text="SHIFT", font=("Segoe UI", 9, "bold"), bg="#1e1e2e", fg="#a6adc8").pack(side="left")
        tk.Label(sub_frame, text=" after typing inputs.", font=("Segoe UI", 9), bg="#1e1e2e", fg="#a6adc8").pack(side="left")

        # Main Rounded Card
        rounded_card = RoundedFrame(self.master, bg_color="#1e1e2e", card_color="#25263a", radius=20)
        rounded_card.pack(fill="both", expand=True, padx=25, pady=10)

        card_container = rounded_card.inner_frame

        for index, (name, category) in enumerate(self.exercise_config):
            row = index // 2
            col = index % 2

            ex_widget = ExerciseRow(
                card_container, 
                name=name, 
                category=category, 
                variable=self.workouts[name],
                pady=4,
                padx=8
            )
            ex_widget.grid(row=row, column=col, sticky="new", padx=6, pady=6)
            card_container.columnconfigure(col, weight=1)
            self.exercise_widgets.append(ex_widget)

        # Buttons
        btn_container = tk.Frame(self.master, bg="#1e1e2e")
        btn_container.pack(fill="x", padx=25, pady=(10, 20))

        self.save_btn = tk.Button(
            btn_container,
            text="SAVE WORKOUT",
            command=self.save_workout,
            bg="#89b4fa",
            fg="#11111b",
            activebackground="#b4befe",
            activeforeground="#11111b",
            font=("Segoe UI", 11, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=10
        )
        self.save_btn.pack(fill="x", pady=(0, 8))

        self.view_btn = tk.Button(
            btn_container,
            text="VIEW SAVED LOGS",
            command=self.view_logs,
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#cdd6f4",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=8
        )
        self.view_btn.pack(fill="x")

        self.save_btn.bind("<Enter>", lambda e: self.save_btn.config(bg="#b4befe"))
        self.save_btn.bind("<Leave>", lambda e: self.save_btn.config(bg="#89b4fa"))
        self.view_btn.bind("<Enter>", lambda e: self.view_btn.config(bg="#45475a"))
        self.view_btn.bind("<Leave>", lambda e: self.view_btn.config(bg="#313244"))

        self.confetti_canvas = ConfettiCanvas(self.master)

    def trigger_confetti(self):
        self.confetti_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.tkraise(self.confetti_canvas)
        self.confetti_canvas.start_confetti()

    def save_workout(self):
        selected_summaries = []
        for widget in self.exercise_widgets:
            summary = widget.get_details()
            if summary:
                selected_summaries.append(summary)

        if selected_summaries:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{now}] " + " | ".join(selected_summaries) + "\n"

            with open(self.log_path, "a") as file:
                file.write(log_line)

            for widget in self.exercise_widgets:
                widget.reset()

            self.trigger_confetti()

            formatted_summary = "\n• ".join(selected_summaries)
            messagebox.showinfo("Workout Saved", f"Log written to workout_log.txt:\n\n• {formatted_summary}")
        else:
            messagebox.showwarning("No Selection", "Please select at least one workout activity.")

    def view_logs(self):
        log_window = tk.Toplevel(self.master)
        log_window.title("Workout History")
        log_window.geometry("480x450")
        log_window.configure(bg="#1e1e2e")

        header_frame = tk.Frame(log_window, bg="#1e1e2e")
        header_frame.pack(side="top", fill="x", padx=15, pady=(15, 5))

        header = tk.Label(
            header_frame, 
            text="SAVED WORKOUT HISTORY", 
            font=("Segoe UI", 12, "bold"), 
            bg="#1e1e2e", 
            fg="#cdd6f4"
        )
        header.pack(side="left")

        bottom_frame = tk.Frame(log_window, bg="#1e1e2e")
        bottom_frame.pack(side="bottom", fill="x", padx=15, pady=15)

        text_frame = tk.Frame(log_window, bg="#25263a")
        text_frame.pack(side="top", fill="both", expand=True, padx=15, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(
            text_frame, 
            wrap="word", 
            yscrollcommand=scrollbar.set,
            bg="#25263a",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Consolas", 10),
            bd=0,
            padx=10,
            pady=10
        )
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

        def populate_logs():
            text_area.config(state="normal")
            text_area.delete("1.0", tk.END)
            if os.path.exists(self.log_path):
                with open(self.log_path, "r") as file:
                    logs = file.read()
                    if logs.strip():
                        text_area.insert("1.0", logs)
                    else:
                        text_area.insert("1.0", "No workout logs found yet.")
            else:
                text_area.insert("1.0", "No workout logs found yet.")
            text_area.config(state="disabled")

        def delete_logs():
            if os.path.exists(self.log_path):
                confirm = messagebox.askyesno(
                    "Confirm Delete", 
                    "Are you sure you want to delete all workout history?",
                    parent=log_window
                )
                if confirm:
                    os.remove(self.log_path)
                    populate_logs()
                    messagebox.showinfo("Deleted", "Workout log history cleared.", parent=log_window)
            else:
                messagebox.showinfo("Info", "No log file to delete.", parent=log_window)

        del_btn = tk.Button(
            bottom_frame,
            text="CLEAR HISTORY",
            command=delete_logs,
            bg="#f38ba8",
            fg="#11111b",
            activebackground="#eba0ac",
            activeforeground="#11111b",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=8
        )
        del_btn.pack(fill="x")

        del_btn.bind("<Enter>", lambda e: del_btn.config(bg="#eba0ac"))
        del_btn.bind("<Leave>", lambda e: del_btn.config(bg="#f38ba8"))

        populate_logs()


if __name__ == "__main__":
    setup_desktop_shortcut()

    # --- Fix 3: Direct className declaration during initialization ---
    root = tk.Tk(className="workout-tracker")
    app = WorkoutApp(root)
    root.mainloop()