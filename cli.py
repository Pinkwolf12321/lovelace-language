# lovelace_cli.py
import sys
from .runtime import LovelaceInterpreter

def main():
    if len(sys.argv) < 2:
        print("Usage: lovelace_cli.py <script.lovelace> [args...]")
        sys.exit(1)
    path = sys.argv[1]
    interp = LovelaceInterpreter(output_fn=lambda s: print(s))
    interp.run_file(path)

if __name__ == "__main__":
    main()
