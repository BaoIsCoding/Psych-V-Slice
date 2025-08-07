import json
import tkinter as tk
from tkinter import filedialog, messagebox

def psych_to_base(data):
    new_data = {
        "name": data.get("character", ""),
        "image": data.get("image", ""),
        "animations": [],
        "scale": data.get("scale", 1.0),
        "flip_x": False,
        "flip_y": False
    }

    anims = data.get("animations", [])
    for anim in anims:
        new_data["animations"].append({
            "anim": anim.get("anim", ""),
            "name": anim.get("name", ""),
            "fps": anim.get("fps", 24),
            "loop": anim.get("loop", True),
            "offsets": [anim.get("offsets", [0, 0])[0], anim.get("offsets", [0, 0])[1]]
        })

    return new_data

def base_to_psych(data):
    new_data = {
        "character": data.get("name", ""),
        "image": data.get("image", ""),
        "animations": [],
        "scale": data.get("scale", 1.0)
    }

    anims = data.get("animations", [])
    for anim in anims:
        new_data["animations"].append({
            "name": anim.get("name", ""),
            "anim": anim.get("anim", ""),
            "fps": anim.get("fps", 24),
            "loop": anim.get("loop", True),
            "offsets": anim.get("offsets", [0, 0])
        })

    return new_data

def select_file():
    filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filepath:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, filepath)

def convert():
    filepath = entry_file.get()
    if not filepath:
        messagebox.showerror("Error", "Please select a file first.")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        mode = var_direction.get()
        if mode == "Psych to Base":
            new_data = psych_to_base(data)
            output_name = filepath.replace(".json", "_base.json")
        else:
            new_data = base_to_psych(data)
            output_name = filepath.replace(".json", "_psych.json")

        with open(output_name, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4)

        messagebox.showinfo("Success", f"Converted file saved as:\n{output_name}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert:\n{e}")

# GUI setup
root = tk.Tk()
root.title("FNF Character Converter")
root.geometry("400x200")
root.resizable(False, False)

tk.Label(root, text="Select Character JSON File:").pack(pady=5)
entry_file = tk.Entry(root, width=40)
entry_file.pack(padx=10)
tk.Button(root, text="Browse", command=select_file).pack(pady=5)

tk.Label(root, text="Conversion Direction:").pack()
var_direction = tk.StringVar()
var_direction.set("Psych to Base")
tk.OptionMenu(root, var_direction, "Psych to Base", "Base to Psych").pack()

tk.Button(root, text="Convert", command=convert).pack(pady=10)

root.mainloop()
