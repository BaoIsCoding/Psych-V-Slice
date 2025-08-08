# FunkinConverter.py
# Multi-file GUI converter for Psych Engine 0.7.3 <-> Base FNF (Character/Chart/Event/Stage/Week)
# Save this file and run with Python 3.

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

# -------------------- Conversion logic --------------------

# ----- Character conversion -----
def psych_char_to_base(data):
    # Drop psych-specific extras, keep essential fields
    return {
        "image": data.get("image", ""),
        "scale": data.get("scale", 1.0),
        "x": data.get("position", [0, 0])[0],
        "y": data.get("position", [0, 0])[1],
        "animations": {
            anim[0]: {
                "anim": anim[1],
                "offset_x": anim[2] if len(anim) > 2 else 0,
                "offset_y": anim[3] if len(anim) > 3 else 0
            } for anim in data.get("animations", [])
        }
    }

def base_char_to_psych(data):
    # Fill psych-expected structure with defaults where missing
    return {
        "image": data.get("image", ""),
        "scale": data.get("scale", 1.0),
        "position": [data.get("x", 0), data.get("y", 0)],
        "animations": [
            [name, info.get("anim", ""), info.get("offset_x", 0), info.get("offset_y", 0)]
            for name, info in data.get("animations", {}).items()
        ]
    }

def detect_char_format(data):
    if isinstance(data.get("animations", None), list):
        return "psych"
    if isinstance(data.get("animations", None), dict):
        return "base"
    if "position" in data and isinstance(data.get("position"), list):
        return "psych"
    if "x" in data and "y" in data:
        return "base"
    return "unknown"

# ----- Chart conversion (Psych 0.7.3 <-> Base) -----
def psych_chart_to_base(data):
    song = data.get("song", {})
    notes_flat = []
    events = song.get("events", [])
    bpm = song.get("bpm", 120)
    for section in song.get("notes", []):
        must = section.get("mustHitSection", True)
        for note in section.get("sectionNotes", []):
            t = note[0]
            nd = note[1] if len(note) > 1 else 0
            sustain = note[2] if len(note) > 2 else 0
            notes_flat.append({
                "strumTime": t,
                "noteData": nd,
                "mustPress": must,
                "sustainLength": sustain
            })
    return {"notes": notes_flat, "events": events, "bpm": bpm}

def base_chart_to_psych(data, bpm=120):
    notes = data.get("notes", [])
    events = data.get("events", [])
    sec_len = (60000 / bpm) * 4
    sections = {}
    for n in notes:
        st = n.get("strumTime", 0)
        idx = int(st // sec_len)
        if idx not in sections:
            sections[idx] = {"sectionNotes": [], "mustHitSection": n.get("mustPress", True)}
        sections[idx]["sectionNotes"].append([n.get("strumTime", 0), n.get("noteData", 0), n.get("sustainLength", 0)])
    ordered = [sections[k] for k in sorted(sections.keys())]
    return {"song": {"notes": ordered, "events": events, "bpm": bpm}}

def detect_chart_format(data):
    if isinstance(data, dict) and "song" in data:
        return "psych"
    if isinstance(data, dict) and "notes" in data and isinstance(data.get("notes"), list):
        return "base"
    return "unknown"

# ----- Events conversion -----
def psych_events_to_base(data):
    if "song" in data:
        return {"events": data["song"].get("events", []), "bpm": data["song"].get("bpm", 120)}
    return {"events": data.get("events", []), "bpm": data.get("bpm", 120)}

def base_events_to_psych(data):
    return {"song": {"events": data.get("events", []), "bpm": data.get("bpm", 120), "notes": []}}

def detect_events_format(data):
    if "song" in data and isinstance(data["song"].get("events", None), list):
        return "psych"
    if "events" in data and isinstance(data.get("events", None), list):
        return "base"
    return "unknown"

# ----- Stage conversion -----
def detect_stage_format(data):
    # heuristics
    if isinstance(data, dict) and ("stage" in data or "objects" in data or "foreground" in data or "background" in data):
        return "psych"
    if isinstance(data, dict) and ("layers" in data or "image" in data or "objects" in data):
        return "base"
    return "unknown"

def psych_stage_to_base(data):
    stage = data.get("stage", data)
    base = {}
    base["image"] = stage.get("image", stage.get("background", ""))
    base["bpm"] = stage.get("bpm", data.get("song", {}).get("bpm", 120))
    base_layers = []
    if "background" in stage:
        base_layers.append({"type": "background", "image": stage.get("background"), "scroll": stage.get("bgScroll", 1.0)})
    if "foreground" in stage:
        base_layers.append({"type": "foreground", "items": stage.get("foreground")})
    objects = stage.get("objects", []) or stage.get("props", []) or []
    base["layers"] = base_layers
    base["objects"] = objects
    base["camera"] = stage.get("camera", {"x": 0, "y": 0})
    if "name" in stage:
        base["name"] = stage.get("name")
    return base

def base_stage_to_psych(data):
    stage = {}
    stage["image"] = data.get("image", data.get("bg", ""))
    stage["bpm"] = data.get("bpm", 120)
    layers = data.get("layers", [])
    for layer in layers:
        if layer.get("type") == "background" and "image" in layer:
            stage["background"] = layer.get("image")
            stage["bgScroll"] = layer.get("scroll", 1.0)
        elif layer.get("type") == "foreground":
            stage["foreground"] = layer.get("items", layer.get("image", []))
    stage["objects"] = data.get("objects", [])
    stage["camera"] = data.get("camera", {"x": 0, "y": 0})
    if "name" in data:
        stage["name"] = data["name"]
    return {"stage": stage}

# ----- Week conversion -----
def detect_week_format(data):
    # Psych often uses "weekBefore" and more fields; base uses simpler week structure
    if isinstance(data, dict) and ("weekBefore" in data or "songs" in data and "unlock" in data):
        return "psych"
    # Base-like week example: { "week": "test", "songs": [...], "weekCharacters": [...] }
    if isinstance(data, dict) and ("weekName" in data or "week" in data or "songs" in data):
        return "base"
    return "unknown"

def psych_week_to_base(data):
    # Keep only vanilla-like fields
    # Psych weeks can be complex; drop extra fields
    week_name = data.get("weekName", data.get("week", "week"))
    songs = data.get("songs", [])
    chars = data.get("weekCharacters", data.get("characters", []))
    # Minimal base week representation
    return {
        "weekName": week_name,
        "weekCharacters": chars,
        "weekSongs": songs,
        # Base game uses simpler unlocked flags
        "startUnlocked": data.get("startUnlocked", True),
        "hiddenUntilUnlocked": data.get("hiddenUntilUnlocked", False)
    }

def base_week_to_psych(data):
    week_name = data.get("weekName", data.get("week", "week"))
    songs = data.get("weekSongs", data.get("songs", []))
    chars = data.get("weekCharacters", data.get("weekCharacters", []))
    # Basic psych-compatible week skeleton
    return {
        "week": week_name,
        "songs": songs,
        "weekCharacters": chars,
        # psych placeholders
        "weekBefore": None,
        "startUnlocked": data.get("startUnlocked", True),
        "hiddenUntilUnlocked": data.get("hiddenUntilUnlocked", False)
    }

# -------------------- Helpers --------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def safe_outpath(orig_path):
    base, ext = os.path.splitext(orig_path)
    return base + "_converted.json"

# Detect type (character/chart/events/stage/week) and sub-format psych/base
def detect_file_type_and_format(data):
    # Character
    if isinstance(data, dict) and ("animations" in data):
        fmt = detect_char_format(data)
        return ("character", fmt)
    # Chart
    if isinstance(data, dict) and ("song" in data or "notes" in data):
        fmt = detect_chart_format(data)
        return ("chart", fmt)
    # Events
    if isinstance(data, dict) and ("events" in data or ("song" in data and "events" in data.get("song", {}))):
        fmt = detect_events_format(data)
        return ("events", fmt)
    # Stage
    if isinstance(data, dict) and detect_stage_format(data) != "unknown":
        fmt = detect_stage_format(data)
        return ("stage", fmt)
    # Week
    if isinstance(data, dict) and detect_week_format(data) != "unknown":
        fmt = detect_week_format(data)
        return ("week", fmt)
    return (None, "unknown")

# Convert function wrapper
def convert_file(path):
    try:
        data = load_json(path)
    except Exception as e:
        return (False, f"JSON load error: {e}")
    filetype, fmt = detect_file_type_and_format(data)
    if filetype is None:
        return (False, "Unknown JSON type/format")
    try:
        if filetype == "character":
            if fmt == "psych":
                out = psych_char_to_base(data)
            else:
                out = base_char_to_psych(data)
        elif filetype == "chart":
            if fmt == "psych":
                out = psych_chart_to_base(data)
            else:
                bpm = data.get("bpm", 120) if isinstance(data, dict) else 120
                out = base_chart_to_psych(data, bpm=bpm)
        elif filetype == "events":
            if fmt == "psych":
                out = psych_events_to_base(data)
            else:
                out = base_events_to_psych(data)
        elif filetype == "stage":
            if fmt == "psych":
                out = psych_stage_to_base(data)
            else:
                out = base_stage_to_psych(data)
        elif filetype == "week":
            if fmt == "psych":
                out = psych_week_to_base(data)
            else:
                out = base_week_to_psych(data)
        else:
            return (False, "Unhandled file type")
        outpath = safe_outpath(path)
        save_json(outpath, out)
        return (True, f"Converted ({filetype}, {fmt}) -> {os.path.basename(outpath)}")
    except Exception as e:
        return (False, f"Conversion error: {e}")

# -------------------- GUI --------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Funkin Converter - Multi Convert (Psych 0.7.3 <-> Base)")
        self.geometry("820x520")
        self.resizable(True, True)
        self.files = []  # list of file paths

        # Top controls
        frm_top = tk.Frame(self)
        frm_top.pack(fill="x", padx=8, pady=6)

        btn_add = tk.Button(frm_top, text="Add Files...", command=self.add_files)
        btn_add.pack(side="left")
        btn_remove = tk.Button(frm_top, text="Remove Selected", command=self.remove_selected)
        btn_remove.pack(side="left", padx=6)
        btn_clear = tk.Button(frm_top, text="Clear", command=self.clear_list)
        btn_clear.pack(side="left", padx=6)
        btn_convert = tk.Button(frm_top, text="Convert All", command=self.convert_all)
        btn_convert.pack(side="right", padx=6)

        # Middle: listbox and log
        middle = tk.PanedWindow(self, orient="horizontal", sashrelief="sunken")
        middle.pack(fill="both", expand=True, padx=8, pady=6)

        # File list
        left = tk.Frame(middle)
        tk.Label(left, text="Files to convert:").pack(anchor="w")
        self.listbox = tk.Listbox(left, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True, padx=2, pady=2)
        middle.add(left, minsize=320)

        # Log panel
        right = tk.Frame(middle)
        tk.Label(right, text="Conversion Log:").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(right, wrap=tk.WORD, height=20)
        self.log.pack(fill="both", expand=True, padx=2, pady=2)
        middle.add(right, minsize=480)

        # Status bar
        self.status = tk.Label(self, text="Ready", anchor="w")
        self.status.pack(fill="x", padx=8, pady=(0,6))

        # allow double-click on listbox item to remove or view
        self.listbox.bind("<Double-Button-1>", self.on_listbox_double)

    # file operations
    def add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if paths:
            for p in paths:
                if p not in self.files:
                    self.files.append(p)
                    self.listbox.insert(tk.END, p)
            self.log_write(f"Added {len(paths)} file(s).")
            self.status.config(text=f"{len(self.files)} file(s) queued")

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        if not sel:
            return
        sel.reverse()
        for i in sel:
            val = self.listbox.get(i)
            if val in self.files:
                self.files.remove(val)
            self.listbox.delete(i)
        self.log_write("Removed selected files.")
        self.status.config(text=f"{len(self.files)} file(s) queued")

    def clear_list(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)
        self.log_write("Cleared file list.")
        self.status.config(text="Ready")

    def convert_all(self):
        if not self.files:
            messagebox.showinfo("Info", "No files to convert.")
            return
        total = len(self.files)
        converted = 0
        self.log_write("Starting conversion of %d file(s)..." % total)
        for i, path in enumerate(self.files[:]):  # iterate over a shallow copy in case of changes
            self.log_write(f"[{i+1}/{total}] Processing: {path}")
            ok, msg = convert_file(path)
            if ok:
                converted += 1
                self.log_write("  OK: " + msg)
            else:
                self.log_write("  ERROR: " + msg)
        self.log_write(f"Finished. Converted {converted}/{total} file(s).")
        self.status.config(text=f"Converted {converted}/{total} file(s)")

    def on_listbox_double(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        path = self.listbox.get(idx)
        # try to open the file location
        try:
            folder = os.path.dirname(path)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f"open \"{folder}\"")
            else:
                os.system(f"xdg-open \"{folder}\"")
        except Exception:
            pass

    def log_write(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

# -------------------- Command-line drag/drop support --------------------
def process_cli_args(args):
    results = []
    for path in args:
        if os.path.isfile(path):
            ok, msg = convert_file(path)
            results.append((path, ok, msg))
            print(f"{path} -> {msg}")
        else:
            print(f"{path} not found.")
    return results

# -------------------- Main --------------------
def main():
    # If files are passed as command-line args, convert them and exit
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        process_cli_args(args)
        print("Done.")
        return

    # else launch GUI
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
