# lovelace_gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from .runtime import LovelaceInterpreter
import os

class LovelaceGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lovelace Runner")
        self.geometry("1000x650")
        self.path = None

        # Menus
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        filem.add_command(label="Open…", command=self.open_file, accelerator="Ctrl+O")
        filem.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        filem.add_command(label="Save As…", command=self.save_as, accelerator="Ctrl+Shift+S")
        filem.add_separator()
        filem.add_command(label="Run ▶", command=self.run_code, accelerator="F5")
        filem.add_separator()
        filem.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filem)
        self.config(menu=menubar)

        # Editor + Output
        self.editor = scrolledtext.ScrolledText(self, undo=True, wrap="none")
        self.editor.pack(fill="both", expand=True)
        self.output = scrolledtext.ScrolledText(self, height=10, bg="#0a0c12", fg="#e7e8ec")
        self.output.pack(fill="x")

        # keybinds
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as())
        self.bind("<F5>", lambda e: self.run_code())

        # starter code
        self.editor.insert("1.0", 'out "Hello, Lovelace!"\n')

    def _print(self, s):
        self.output.insert("end", str(s) + "\n")
        self.output.see("end")

    def new_file(self):
        self.path = None
        self.editor.delete("1.0", "end")
        self.output.delete("1.0", "end")
        self._update_title()

    def open_file(self):
        p = filedialog.askopenfilename(filetypes=[("Lovelace Script", "*.lovelace"), ("All files","*.*")])
        if not p: return
        with open(p, "r", encoding="utf-8") as f:
            src = f.read()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", src)
        self.path = p
        self._update_title()

    def save_file(self):
        if not self.path:
            return self.save_as()
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self.editor.get("1.0", "end-1c"))
        self._update_title()
        self._print(f"[saved] {self.path}")

    def save_as(self):
        p = filedialog.asksaveasfilename(defaultextension=".lovelace", filetypes=[("Lovelace Script", "*.lovelace")])
        if not p: return
        self.path = p
        self.save_file()

    def run_code(self):
        self.output.delete("1.0", "end")
        src = self.editor.get("1.0", "end-1c")
        interp = LovelaceInterpreter(output_fn=self._print)
        try:
            interp.run_string(src)
        except Exception as e:
            self._print(f"[error] {e}")

    def _update_title(self):
        name = self.path if self.path else "Untitled.lovelace"
        self.title(f"Lovelace Runner — {os.path.basename(name)}")

if __name__ == "__main__":
    LovelaceGUI().mainloop()
