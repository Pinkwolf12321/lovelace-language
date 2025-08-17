# Lovelace
Lovelace is a minimal-but-real scripting language runtime and editor written in Python.
It supports variable assignments, memory arrays, loops, functions, and simple I/O.

This project provides:
- Runtime: Execute .lovelace scripts (runtime.py)
- CLI: Run scripts from the command line (cli.py)
- GUI: A simple Tkinter-based IDE for writing, saving,and running scripts (gui.py)

### Features
- Variables
- Memory Arrays
- Output
- Sleep
- Conditional Statements
- Loops
- Functions
- Spawn

### Installation
Clone the repo and install as package:
    
```
git clone https://github.com/pinkwolf12321/lovelace.git
cd lovelace
pip install -e .
```

### Usage
```
cd lovelace
```
CLI:
    
```
python -m cli.py my_script.lovelace
```

GUI:
    
```
python -m gui.py
```

### File Extension
Scripts use the .lovelace file extension.

### Example
```
var greeting ("Hello, Lovelace!")
out greeting

loop (3):
out "Looping..."
end
```

### Contributing
PRs and suggestions welcome! Make sure to test your scripts in both CLI and GUI before submitting.

### License
Lovelace Programming Language © Blyth Laiman Karl 2025. All Rights Reserved.
