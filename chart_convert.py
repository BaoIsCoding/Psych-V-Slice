import json
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def psych_to_base_chart(psych_data):
    base_chart = []

    for section in psych_data["song"]["notes"]:
        mustHit = section.get("mustHitSection", True)
        for note in section.get("sectionNotes", []):
            time = note[0]
            noteData = note[1]
            sustain = note[2] if len(note) > 2 else 0
            base_chart.append({
                "strumTime": time,
                "noteData": noteData,
                "mustPress": mustHit,
                "sustainLength": sustain
            })

    return base_chart

def base_to_psych_chart(base_data, bpm=120):
    psych_chart = {
        "song": {
            "notes": [],
            "bpm": bpm
        }
    }

    section_length_ms = (60000 / bpm) * 4
    sections = {}

    for note in base_data:
        section_index = int(note["strumTime"] // section_length_ms)
        if section_index not in sections:
            sections[section_index] = {
                "sectionNotes": [],
                "mustHitSection": note["mustPress"]
            }
        sections[section_index]["sectionNotes"].append([
            note["strumTime"],
            note["noteData"],
            note.get("sustainLength", 0)
        ])

    for i in sorted(sections.keys()):
        psych_chart["song"]["notes"].append(sections[i])

    return psych_chart

def convert_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        if "song" in data and "notes" in data["song"]:
            # Psych ➜ Base
            converted = psych_to_base_chart(data)
            out_path = path.replace(".json", "_to_base.json")
        else:
            # Base ➜ Psych
            converted = base_to_psych_chart(data, bpm=120)
            out_path = path.replace(".json", "_to_psych.json")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(converted, f, indent=2)

        messagebox.showinfo("Conversion Done", f"Saved: {os.path.basename(out_path)}")

    except Exception as e:
        messagebox.showerror("Error", f"Could not convert: {e}")

def choose_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        convert_file(file_path)

# GUI
root = tk.Tk()
root.title("FNF Chart Converter (Psych <-> Base Game)")
root.geometry("400x150")
tk.Label(root, text="🎵 Drag and drop .json chart to convert").pack(pady=10)
tk.Button(root, text="Select Chart File", command=choose_file).pack()
tk.Label(root, text="Auto-detects Psych or Base chart.").pack(pady=10)
root.mainloop()
