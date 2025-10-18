import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta, date
from collections import defaultdict
import os
import sys
import random

# This app requires the 'pygame' library for music. Install it with: pip install pygame
try:
    import pygame
except ImportError:
    messagebox.showerror("Missing Dependency", "The 'pygame' library is required for music playback.\nPlease install it by running: pip install pygame")
    pygame = None

# --- CONSTANTS ---
DATA_FILE = "productivity_data.json"
# Prefer .ogg for better compatibility, fall back to .mp3
MUSIC_FILES = ("music.ogg", "music.mp3", "music2.ogg", "music2.mp3")

# Pokemon Red theme colors
PRIMARY_COLOR = "#f8f8f8"  # Gameboy screen background
SECONDARY_COLOR = "#e0e0e0" # Lighter grey for elements
TEXT_COLOR = "#0f380f"    # Dark olive green text
ACCENT_COLOR = "#d82800"   # Pokemon Red
SUCCESS_COLOR = "#30a850"  # A fitting green
BORDER_COLOR = "#8b0000"  # Dark Red for borders

# Pokemon Red theme font
FONT_FAMILY = "Fixedsys" # A classic blocky/pixel font
ALT_FONT_FAMILY = "Courier New" # Fallback if Fixedsys isn't available

# --- UTILITY FUNCTIONS ---
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- DATA HANDLING ---
def load_data():
    """Loads tasks and time logs from a JSON file."""
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Ensure keys exist, provide defaults if not
            if "tasks" not in data:
                data["tasks"] = []
            if "time_logs" not in data:
                data["time_logs"] = {}
            if "weight_logs" not in data:
                data["weight_logs"] = {}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty/corrupt, return a default structure
        return {"tasks": [], "time_logs": {}, "weight_logs": {}}
    except Exception as e:
        # Catch other potential file reading errors (e.g., permissions)
        messagebox.showerror("Error Loading Data", f"Could not read the data file:\n{e}")
        return {"tasks": [], "time_logs": {}, "weight_logs": {}}

def save_data(data):
    """Saves the given data structure to the JSON file."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        # Catch potential file writing errors (e.g., permissions)
        messagebox.showerror("Error Saving Data", f"Could not save to the data file:\n{e}")

# --- MAIN APPLICATION CLASS ---
class ProductivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vibe Code Productivity")
        self.root.geometry("600x700") # Increased height for stats
        self.root.configure(bg=PRIMARY_COLOR)

        # --- STATE VARIABLES ---
        self.data = load_data()
        self.backfill_missed_days() # Add 0s for missed days
        self.timer_running = False
        self.start_time = None
        self.music_playing = False
        self.music_loaded = False
        
        # --- STYLING ---
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.configure_styles()

        # --- UI SETUP ---
        self.create_widgets()
        self.setup_music_player()
        self.update_task_list()
        self.update_time_log_display()
        self.update_weight_ui()
        self.update_stats_display()


        # --- CLEAN SHUTDOWN ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handles the window closing event to clean up resources."""
        if pygame:
            pygame.quit()
        self.root.destroy()

    def configure_styles(self):
        """Configures the visual styles for ttk widgets."""
        font_to_use = FONT_FAMILY
        try:
            # Check if font is available
            self.root.tk.call('font', 'actual', (font_to_use, 10))
        except tk.TclError:
            font_to_use = ALT_FONT_FAMILY # Fallback

        self.style.configure("TNotebook", background=PRIMARY_COLOR, borderwidth=2)
        self.style.configure("TNotebook.Tab", background=SECONDARY_COLOR, foreground=TEXT_COLOR, padding=[10, 5], font=(font_to_use, 10, 'bold'), borderwidth=2, relief='raised')
        self.style.map("TNotebook.Tab", background=[("selected", ACCENT_COLOR)], foreground=[("selected", PRIMARY_COLOR)])
        
        self.style.configure("TFrame", background=PRIMARY_COLOR)
        self.style.configure("TLabel", background=PRIMARY_COLOR, foreground=TEXT_COLOR, font=(font_to_use, 11))
        
        self.style.configure("TButton", background=SECONDARY_COLOR, foreground=TEXT_COLOR, font=(font_to_use, 10, 'bold'), borderwidth=2, relief="raised", padding=10)
        self.style.map("TButton", background=[('active', '#cccccc')])
        
        self.style.configure("Success.TButton", foreground=SUCCESS_COLOR)
        
        self.style.configure("Treeview", rowheight=25, fieldbackground=PRIMARY_COLOR, background=PRIMARY_COLOR, foreground=TEXT_COLOR, font=(font_to_use, 10))
        self.style.map("Treeview", background=[("selected", ACCENT_COLOR)], foreground=[("selected", PRIMARY_COLOR)])
        self.style.configure("Treeview.Heading", font=(font_to_use, 11, 'bold'), background=SECONDARY_COLOR, foreground=TEXT_COLOR, relief="raised", borderwidth=2)
        self.style.map("Treeview.Heading", background=[('active', SECONDARY_COLOR)])
        
        self.style.configure("TEntry", fieldbackground=PRIMARY_COLOR, foreground=TEXT_COLOR, insertcolor=TEXT_COLOR, bordercolor=TEXT_COLOR, lightcolor=PRIMARY_COLOR, darkcolor=PRIMARY_COLOR)
        self.style.configure("Horizontal.TScale", background=PRIMARY_COLOR)


    def create_widgets(self):
        """Creates and arranges all the UI elements."""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both")

        notebook = ttk.Notebook(main_frame)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- TABS ---
        tasks_frame = ttk.Frame(notebook, padding="10")
        notebook.add(tasks_frame, text="Tasks")
        self.create_tasks_tab(tasks_frame)

        timer_frame = ttk.Frame(notebook, padding="10")
        notebook.add(timer_frame, text="Focus Timer")
        self.create_timer_tab(timer_frame)
        
        weight_frame = ttk.Frame(notebook, padding="10")
        notebook.add(weight_frame, text="Weight Tracker")
        self.create_weight_tab(weight_frame)

        stats_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stats_frame, text="Stats")
        self.create_stats_tab(stats_frame)
        
        # --- MUSIC PLAYER FRAME ---
        music_frame = ttk.Frame(main_frame, style="TFrame", relief='groove', borderwidth=2)
        music_frame.pack(fill='x', padx=10, pady=(0, 10))
        self.music_button = ttk.Button(music_frame, text="Play Music", command=self.toggle_music, state="disabled")
        self.music_button.pack(pady=5)
        
        self.volume_slider = ttk.Scale(music_frame, from_=0, to=100, orient="horizontal", command=self.set_volume, style="Horizontal.TScale")
        self.volume_slider.set(70) # Set default volume to 70%
        self.volume_slider.pack(fill='x', padx=10, pady=(0, 5))


    def create_tasks_tab(self, parent_frame):
        """Creates the widgets for the task management tab."""
        input_frame = ttk.Frame(parent_frame, style="TFrame")
        input_frame.pack(fill="x", pady=5)

        self.task_entry = ttk.Entry(input_frame, font=(FONT_FAMILY, 12), style="TEntry")
        self.task_entry.pack(side="left", fill="x", expand=True, ipady=5)
        
        add_button = ttk.Button(input_frame, text="Create Task", command=self.add_task)
        add_button.pack(side="left", padx=(5, 0))

        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.task_listbox = tk.Listbox(list_frame, font=(FONT_FAMILY, 12), bg=PRIMARY_COLOR, fg=TEXT_COLOR, selectbackground=ACCENT_COLOR, selectforeground=PRIMARY_COLOR, activestyle="none", borderwidth=2, highlightthickness=2, highlightcolor=BORDER_COLOR, relief="solid")
        self.task_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.task_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.task_listbox.config(yscrollcommand=scrollbar.set)
        
        check_button = ttk.Button(parent_frame, text="Check Task", style="Success.TButton", command=self.complete_task)
        check_button.pack(fill="x", pady=5)

    def create_timer_tab(self, parent_frame):
        """Creates the widgets for the timer and time log tab."""
        self.timer_label = ttk.Label(parent_frame, text="00:00:00", font=(FONT_FAMILY, 48, 'bold'), anchor="center", foreground=ACCENT_COLOR)
        self.timer_label.pack(pady=20)

        self.timer_button = ttk.Button(parent_frame, text="Start Timer", command=self.toggle_timer)
        self.timer_button.pack(pady=10, ipadx=20)
        
        self.weekly_study_avg_label = ttk.Label(parent_frame, text="This Week's Avg: 0 hours 0 mins", font=(FONT_FAMILY, 10, 'bold'), anchor="center")
        self.weekly_study_avg_label.pack(pady=(5, 5))

        log_label = ttk.Label(parent_frame, text="Focus Log", font=(FONT_FAMILY, 14, 'bold'), anchor="center")
        log_label.pack(pady=(10, 5))

        columns = ("day", "time_studied")
        self.time_log_tree = ttk.Treeview(parent_frame, columns=columns, show="headings")
        self.time_log_tree.heading("day", text="Day")
        self.time_log_tree.heading("time_studied", text="Time Studied")
        self.time_log_tree.column("day", width=200)
        self.time_log_tree.pack(fill="both", expand=True)

    def create_weight_tab(self, parent_frame):
        """Creates the widgets for the weight tracker tab."""
        self.today_weight_frame = ttk.Frame(parent_frame)
        self.today_weight_frame.pack(fill="x", pady=10)

        self.weight_input_label = ttk.Label(self.today_weight_frame, text="Today's Weight:", font=(FONT_FAMILY, 12, 'bold'))
        self.weight_entry = ttk.Entry(self.today_weight_frame, font=(FONT_FAMILY, 12))
        self.save_weight_button = ttk.Button(self.today_weight_frame, text="Save Weight", command=self.save_weight, style="Success.TButton")
        self.weight_display_label = ttk.Label(self.today_weight_frame, font=(FONT_FAMILY, 12), foreground=SUCCESS_COLOR)
        
        self.avg_weight_label = ttk.Label(parent_frame, text="Average Weight: N/A", font=(FONT_FAMILY, 10, 'bold'), anchor="center")
        self.avg_weight_label.pack(pady=(5, 5))

        history_label = ttk.Label(parent_frame, text="Weight History", font=(FONT_FAMILY, 14, 'bold'), anchor="center")
        history_label.pack(pady=5)
        
        columns = ("day", "weight")
        self.weight_log_tree = ttk.Treeview(parent_frame, columns=columns, show="headings")
        self.weight_log_tree.heading("day", text="Day")
        self.weight_log_tree.heading("weight", text="Weight")
        self.weight_log_tree.column("day", width=200)
        self.weight_log_tree.pack(fill="both", expand=True)

    def create_stats_tab(self, parent_frame):
        """Creates the widgets for the statistics tab."""
        stats_container = ttk.Frame(parent_frame)
        stats_container.pack(fill="both", expand=True, pady=10)

        self.total_hours_label = ttk.Label(stats_container, text="Total Hours Studied: 0", font=(FONT_FAMILY, 12, 'bold'))
        self.total_hours_label.pack(anchor="w", pady=5)
        
        self.total_hours_this_week_label = ttk.Label(stats_container, text="Total Hours This Week: 0", font=(FONT_FAMILY, 12, 'bold'))
        self.total_hours_this_week_label.pack(anchor="w", pady=5)
        
        self.weight_change_label = ttk.Label(stats_container, text="Total Weight Change: N/A", font=(FONT_FAMILY, 12, 'bold'))
        self.weight_change_label.pack(anchor="w", pady=5)

        weekly_avg_label = ttk.Label(stats_container, text="Weekly Study Averages (Per Day)", font=(FONT_FAMILY, 14, 'bold'))
        weekly_avg_label.pack(pady=(20, 5))
        
        columns = ("week", "avg_time")
        self.weekly_avg_tree = ttk.Treeview(stats_container, columns=columns, show="headings")
        self.weekly_avg_tree.heading("week", text="Week of")
        self.weekly_avg_tree.heading("avg_time", text="Average Study Time")
        self.weekly_avg_tree.pack(fill="both", expand=True)

    # --- MUSIC LOGIC ---
    def setup_music_player(self):
        """Initializes the music player and loads a random song."""
        if not pygame:
            self.music_button.config(text="Pygame not found")
            return

        available_music = []
        for music_file in MUSIC_FILES:
            path = get_resource_path(music_file)
            if os.path.exists(path):
                available_music.append(path)

        try:
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            if available_music:
                music_path_to_load = random.choice(available_music)
                pygame.mixer.music.load(music_path_to_load)
                self.set_volume(self.volume_slider.get())
                self.music_button.config(state="normal")
                self.music_loaded = True
                self.toggle_music() # Auto-play music
            else:
                 self.music_button.config(text="Music file not found")
        except Exception as e:
            messagebox.showerror("Music Error", f"Could not initialize music player:\n{e}")
            self.music_button.config(text="Music Init Error")

    def set_volume(self, val):
        """Sets the music volume based on the slider value."""
        if self.music_loaded:
            try:
                volume = float(val) / 100
                pygame.mixer.music.set_volume(volume)
            except Exception:
                pass 

    def toggle_music(self):
        """Plays or pauses the music."""
        if not self.music_loaded:
            return
        try:
            if self.music_playing:
                pygame.mixer.music.pause()
                self.music_playing = False
                self.music_button.config(text="Play Music")
            else:
                if not pygame.mixer.music.get_busy():
                     pygame.mixer.music.play(loops=-1)
                else:
                     pygame.mixer.music.unpause()
                self.music_playing = True
                self.music_button.config(text="Pause Music")
        except Exception as e:
            messagebox.showerror("Playback Error", f"Could not play music:\n{e}")


    # --- TASK LOGIC ---
    def add_task(self):
        task = self.task_entry.get()
        if task:
            self.data["tasks"].append(task)
            save_data(self.data)
            self.update_task_list()
            self.task_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Empty Task", "Please enter a task description.")

    def complete_task(self):
        selected_indices = self.task_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a task to complete.")
            return
        for index in sorted(selected_indices, reverse=True):
            self.data["tasks"].pop(index)
        save_data(self.data)
        self.update_task_list()

    def update_task_list(self):
        self.task_listbox.delete(0, tk.END)
        for task in self.data["tasks"]:
            self.task_listbox.insert(tk.END, task)

    # --- TIMER LOGIC ---
    def backfill_missed_days(self):
        """Adds 0-second entries for any days missed since the last entry."""
        if not self.data["time_logs"]:
            return

        valid_dates = []
        for date_str in self.data["time_logs"].keys():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                valid_dates.append(dt.date())
            except ValueError:
                print(f"Warning: Skipping malformed date string '{date_str}' in time_logs.")
                continue

        if not valid_dates:
            return

        sorted_dates = sorted(valid_dates)
        last_date = sorted_dates[-1]
        today = date.today()
        
        delta = today - last_date
        if delta.days <= 1:
            return # No missed days to fill or only yesterday

        date_to_fill = last_date + timedelta(days=1)
        updated = False
        while date_to_fill < today:
            date_str = date_to_fill.strftime("%Y-%m-%d")
            if date_str not in self.data["time_logs"]:
                self.data["time_logs"][date_str] = 0
                updated = True
            date_to_fill += timedelta(days=1)
        
        if updated:
            save_data(self.data)

    def toggle_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.timer_button.config(text="Start Timer")
            self.record_time()
        else:
            self.timer_running = True
            self.timer_button.config(text="Stop Timer")
            self.start_time = datetime.now()
            self.update_timer_display()

    def update_timer_display(self):
        if self.timer_running:
            elapsed = datetime.now() - self.start_time
            formatted_time = str(timedelta(seconds=int(elapsed.total_seconds())))
            self.timer_label.config(text=formatted_time)
            self.root.after(1000, self.update_timer_display)

    def record_time(self):
        if self.start_time:
            elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
            today_str = datetime.now().strftime("%Y-%m-%d")
            current_total_seconds = self.data["time_logs"].get(today_str, 0)
            new_total_seconds = current_total_seconds + elapsed_seconds
            self.data["time_logs"][today_str] = new_total_seconds
            save_data(self.data)
            self.update_time_log_display()
            self.update_stats_display()

    def format_seconds(self, total_seconds, precise=False):
        """Formats total seconds into a human-readable string."""
        seconds = int(total_seconds)
        if seconds < 60 and not precise:
            return f"{seconds} secs"
        
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} min{'s' if minutes > 1 else ''}")
        if not parts and secs >= 0 and precise:
             parts.append(f"{secs} sec{'s' if secs != 1 else ''}")

        return " ".join(parts) if parts else "0 mins"

    def update_time_log_display(self):
        for item in self.time_log_tree.get_children():
            self.time_log_tree.delete(item)
        
        # Filter out bad dates before sorting
        valid_logs = {}
        for date_str, seconds in self.data["time_logs"].items():
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                valid_logs[date_str] = seconds
            except ValueError:
                continue # Skip bad dates

        sorted_logs = sorted(valid_logs.items(), key=lambda item: item[0], reverse=True)
        
        # Calculate this week's average for the label
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        this_week_seconds = 0
        days_in_week_so_far = (today - start_of_week).days + 1
        
        for date_str, total_seconds in sorted_logs:
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if log_date >= start_of_week:
                this_week_seconds += total_seconds

        avg_this_week_seconds = this_week_seconds / days_in_week_so_far
        self.weekly_study_avg_label.config(text=f"This Week's Avg: {self.format_seconds(avg_this_week_seconds, precise=True)}")


        for date_str, total_seconds in sorted_logs:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_day = date_obj.strftime("%A, %B %d")
            except ValueError:
                display_day = date_str
            display_time = self.format_seconds(total_seconds)
            self.time_log_tree.insert("", tk.END, values=(display_day, display_time))
    
    # --- WEIGHT LOGIC ---
    def save_weight(self):
        weight_str = self.weight_entry.get()
        try:
            weight = float(weight_str)
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.data["weight_logs"][today_str] = weight
            save_data(self.data)
            self.update_weight_ui()
            self.update_stats_display()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the weight.")
        self.weight_entry.delete(0, tk.END)
        
    def update_weight_ui(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        self.weight_input_label.pack_forget()
        self.weight_entry.pack_forget()
        self.save_weight_button.pack_forget()
        self.weight_display_label.pack_forget()

        if today_str in self.data["weight_logs"]:
            logged_weight = self.data["weight_logs"][today_str]
            self.weight_display_label.config(text=f"Today's logged weight: {logged_weight}")
            self.weight_display_label.pack()
        else:
            self.weight_input_label.pack(side="left", padx=5)
            self.weight_entry.pack(side="left", fill="x", expand=True, ipady=2)
            self.save_weight_button.pack(side="left", padx=5)
            
        self.update_weight_history_display()

    def update_weight_history_display(self):
        for item in self.weight_log_tree.get_children():
            self.weight_log_tree.delete(item)
            
        if not self.data["weight_logs"]:
            self.avg_weight_label.config(text="Average Weight: N/A")
            return

        total_weight = sum(self.data["weight_logs"].values())
        avg_weight = total_weight / len(self.data["weight_logs"])
        self.avg_weight_label.config(text=f"Average Weight: {avg_weight:.2f}")

        sorted_dates = sorted(self.data["weight_logs"].keys())
        start_date = datetime.strptime(sorted_dates[0], "%Y-%m-%d")
        end_date = datetime.now()
        
        filled_logs = []
        last_known_weight = None
        current_date = start_date

        while current_date <= end_date:
            current_date_str = current_date.strftime("%Y-%m-%d")
            if current_date_str in self.data["weight_logs"]:
                last_known_weight = self.data["weight_logs"][current_date_str]
            if last_known_weight is not None:
                display_day = current_date.strftime("%A, %B %d")
                filled_logs.append((display_day, last_known_weight))
            current_date += timedelta(days=1)
        
        for day, weight in reversed(filled_logs):
            self.weight_log_tree.insert("", tk.END, values=(day, weight))

    # --- STATS LOGIC ---
    def update_stats_display(self):
        """Calculates and updates all labels in the stats tab."""
        # 1. Total hours studied
        total_seconds = sum(self.data["time_logs"].values())
        total_hours = total_seconds / 3600
        self.total_hours_label.config(text=f"Total Hours Studied: {total_hours:.2f}")

        # 2. This week's total hours
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        this_week_seconds = 0
        for date_str, seconds in self.data["time_logs"].items():
            try:
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if log_date >= start_of_week:
                    this_week_seconds += seconds
            except ValueError:
                continue
        this_week_hours = this_week_seconds / 3600
        self.total_hours_this_week_label.config(text=f"Total Hours This Week: {this_week_hours:.2f}")

        # 3. Total weight lost/gained
        if len(self.data["weight_logs"]) > 1:
            sorted_weights = sorted(self.data["weight_logs"].items())
            first_weight = sorted_weights[0][1]
            latest_weight = sorted_weights[-1][1]
            change = latest_weight - first_weight
            change_text = f"Gained {abs(change):.2f}" if change > 0 else f"Lost {abs(change):.2f}"
            self.weight_change_label.config(text=f"Total Weight Change: {change_text}")
        else:
            self.weight_change_label.config(text="Total Weight Change: N/A")

        # 4. Each week's average
        for item in self.weekly_avg_tree.get_children():
            self.weekly_avg_tree.delete(item)
            
        weekly_data = defaultdict(list)
        for date_str, seconds in self.data["time_logs"].items():
            try:
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start_of_week = log_date - timedelta(days=log_date.weekday())
                weekly_data[start_of_week].append(seconds)
            except ValueError:
                continue
        
        sorted_weeks = sorted(weekly_data.keys(), reverse=True)
        for week_start_date in sorted_weeks:
            days_with_entries = len(weekly_data[week_start_date])
            if days_with_entries == 0: continue
            
            total_seconds_in_week = sum(weekly_data[week_start_date])
            avg_daily_seconds = total_seconds_in_week / 7 # Average over the whole week
            week_label = week_start_date.strftime("Week of %b %d, %Y")
            avg_display = self.format_seconds(avg_daily_seconds, precise=True)
            self.weekly_avg_tree.insert("", tk.END, values=(week_label, avg_display))


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductivityApp(root)
    root.mainloop()

