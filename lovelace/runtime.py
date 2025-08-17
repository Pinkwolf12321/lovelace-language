# lovelace_interpreter.py
# Minimal-but-real Lovelace interpreter (Python 3.12)
# Supports:
#  - comments ### ...
#  - var x (expr)
#  - mem[i] = expr   /  mem[i] reads in expr
#  - out expr
#  - sleep(seconds)
#  - if/elif/else ... end
#  - loop (N): ... end
#  - loop arr: ... end
#  - fn name(args) => expr
#  - fn name(args): ... end + return expr
#  - spawn (n) (name1, name2, ...) and spawn (n) (RAN) [simulated]

from __future__ import annotations
from dataclasses import dataclass
import time
import random
import re
from typing import Any, Dict, List, Tuple, Callable

@dataclass
class Function:
    args: List[str]
    expr: str | None = None
    body: List[str] | None = None  # lines inside fn ... end

class LovelaceInterpreter:
    def __init__(self, output_fn=print):
        self.vars: Dict[str, Any] = {}
        self.mem: Dict[int, Any] = {}
        self.funcs: Dict[str, Function] = {}
        self.output = output_fn
        self.__apps = ["chrome","edge","firefox","safari","opera","notepad","calc","vscode","terminal"]

    # ------------- Public API -------------
    def run_string(self, src: str):
        lines = self._preprocess(src)
        self._exec_block(lines, 0, len(lines))

    def run_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.run_string(f.read())

    # ------------- Core executor -------------
    def _preprocess(self, src: str) -> List[str]:
        out = []
        for raw in src.replace("\r\n","\n").replace("\r","\n").split("\n"):
            # strip comments
            line = re.sub(r"###.*$", "", raw).rstrip()
            if line.strip():
                out.append(line)
        return out

    def _exec_block(self, lines: List[str], start: int, end: int) -> int:
        i = start
        while i < end:
            line = lines[i].strip()

            # end (handled by caller)
            if line == "end":
                return i + 1

            # var NAME (expr)
            m = re.match(r"^var\s+([A-Za-z_]\w*)\s*\((.+)\)\s*$", line)
            if m:
                name, expr = m.groups()
                self.vars[name] = self._eval(expr)
                i += 1
                continue

            # mem[idx] = expr
            m = re.match(r"^mem\[(.+?)\]\s*=\s*(.+)$", line)
            if m:
                idx_expr, rhs = m.groups()
                idx_val = int(self._eval(idx_expr))
                self.mem[idx_val] = self._eval(rhs)
                i += 1
                continue

            # out expr
            m = re.match(r"^out\s+(.+)$", line)
            if m:
                self.output(self._eval(m.group(1)))
                i += 1
                continue

            # sleep(seconds)
            m = re.match(r"^sleep\((.+)\)\s*$", line)
            if m:
                secs = float(self._eval(m.group(1)))
                time.sleep(max(0.0, secs))
                i += 1
                continue

            # spawn (count) (list|RAN)
            m = re.match(r"^spawn\s*\((.+)\)\s*\((.+)\)\s*$", line)
            if m:
                count_expr, list_part = m.groups()
                count = int(self._eval(count_expr))
                if list_part.strip().upper() == "RAN":
                    for _ in range(count):
                        app = random.choice(self.__apps)
                        self.output(f"[spawn] {app} (simulated)")
                else:
                    names = [s.strip() for s in list_part.split(",") if s.strip()]
                    for _ in range(count):
                        app = random.choice(names) if names else "unknown"
                        self.output(f"[spawn] {app} (simulated)")
                i += 1
                continue

            # if (...) :    / elif (...) :   / else:
            if re.match(r"^if\s*\(.+\):\s*$", line):
                i = self._handle_if(lines, i, end)
                continue

            if re.match(r"^elif\s*\(.+\):\s*$", line) or line == "else:":
                # these should be consumed inside _handle_if
                raise RuntimeError("‘elif/else’ without matching ‘if’")

            # loop (N):
            m = re.match(r"^loop\s*\((.+)\):\s*$", line)
            if m:
                i = self._handle_loop_count(lines, i, end, m.group(1))
                continue

            # loop arr:
            m = re.match(r"^loop\s+([A-Za-z_]\w*):\s*$", line)
            if m:
                i = self._handle_loop_each(lines, i, end, m.group(1))
                continue

            # fn name(args) => expr
            m = re.match(r"^fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*=>\s*(.+)$", line)
            if m:
                name, arglist, expr = m.groups()
                args = [a.strip() for a in arglist.split(",") if a.strip()]
                self.funcs[name] = Function(args=args, expr=expr)
                i += 1
                continue

            # fn name(args):
            m = re.match(r"^fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\):\s*$", line)
            if m:
                name, arglist = m.groups()
                args = [a.strip() for a in arglist.split(",") if a.strip()]
                # find matching end
                body_start = i + 1
                j = body_start
                depth = 1
                while j < end and depth > 0:
                    t = lines[j].strip()
                    if re.match(r"^fn\s+[A-Za-z_]\w*\s*\([^)]*\):\s*$", t) or re.match(r"^if\s*\(.+\):\s*$", t) or re.match(r"^loop\s*(\(|[A-Za-z_])", t):
                        depth += 1
                    elif t == "end":
                        depth -= 1
                    j += 1
                body = lines[body_start:j-1]
                self.funcs[name] = Function(args=args, body=body)
                i = j
                continue

            # return expr (only valid in fn body)
            if re.match(r"^return\s+.+$", line):
                # Handled by function executor; if we get here, it's a stray return
                raise RuntimeError("‘return’ used outside of a function")

            # bare function calls (e.g., foo(1,2))
            m = re.match(r"^([A-Za-z_]\w*)\(([^)]*)\)\s*$", line)
            if m:
                self._call_func(m.group(1), [a.strip() for a in m.group(2).split(",")] if m.group(2).strip() else [])
                i += 1
                continue

            raise RuntimeError(f"Unrecognized syntax: {line}")
        return i

    # ------------- Helpers -------------
    def _eval(self, expr: str) -> Any:
        # Replace mem[i] reads for Python eval
        def mem_read(m):
            idx = int(self._eval(m.group(1)))
            return repr(self.mem.get(idx, 0))
        expr_py = re.sub(r"mem\[(.+?)\]", mem_read, expr)

        # Safe-ish eval environment
        env = {
            "str": str, "int": int, "float": float, "bool": bool, "num": float,
            "RAN_int": lambda a,b: random.randint(int(a), int(b)),
            "RAN_pick": lambda arr: random.choice(list(arr)),
        }
        # add variables by value
        env.update(self.vars)
        try:
            return eval(expr_py, {"__builtins__": {}}, env)
        except Exception:
            # Treat as string literal if not quoted? fall back to raw
            return expr.strip('"')

    def _call_func(self, name: str, arg_exprs: List[str]) -> Any:
        if name not in self.funcs:
            raise RuntimeError(f"Unknown function: {name}")
        fn = self.funcs[name]
        args_vals = [self._eval(a) for a in arg_exprs]

        if fn.expr is not None:
            # expression fn
            local = dict(zip(fn.args, args_vals))
            # Evaluate expression with locals
            env = dict(self.vars)
            env.update(local)
            expr = fn.expr
            # allow mem[] reads
            def mem_read(m):
                idx = int(self._eval(m.group(1)))
                return repr(self.mem.get(idx, 0))
            expr_py = re.sub(r"mem\[(.+?)\]", mem_read, expr)
            return eval(expr_py, {"__builtins__": {}}, env)

        # block fn: execute body with a small call frame
        frame_vars_backup = dict(self.vars)
        try:
            for k, v in zip(fn.args, args_vals):
                self.vars[k] = v
            # run lines until 'return'
            i = 0
            while i < len(fn.body or []):
                line = (fn.body or [])[i].strip()
                if line.startswith("return "):
                    return self._eval(line[len("return "):])
                # Execute a mini-block by reusing executor on a single line or nested structures
                # We delegate by crafting a small temporary program
                self._exec_block([line], 0, 1)
                i += 1
        finally:
            self.vars = frame_vars_backup

    def _handle_if(self, lines: List[str], i: int, end: int) -> int:
        # find whole if/elif/else group up to matching end
        j = i + 1
        depth = 1
        blocks: List[Tuple[str | None, Tuple[int,int]]] = []  # (condition or None for else, (start,end))
        # current block start right after the if/elif/else line
        cur_start = j

        headers = [(i, lines[i].strip())]

        while j < end and depth > 0:
            t = lines[j].strip()
            if re.match(r"^if\s*\(.+\):\s*$", t) or re.match(r"^loop\s*(\(|[A-Za-z_])", t) or re.match(r"^fn\s+[A-Za-z_]\w*\s*\([^)]*\):\s*$", t):
                depth += 1
            elif t == "end":
                depth -= 1
                if depth == 0:
                    # close last block
                    headers.append((j, "end"))
                    break
            elif depth == 1 and (re.match(r"^elif\s*\(.+\):\s*$", t) or t == "else:"):
                headers.append((j, t))
            j += 1

        # Build block ranges
        # headers like: (if_line), (elif_line)?, (else_line)?, (end_line)
        for idx in range(len(headers)-1):
            line_idx, hdr = headers[idx]
            next_idx, _ = headers[idx+1]
            start_block = line_idx + 1
            end_block = next_idx
            if hdr.startswith("if"):
                cond = hdr[hdr.find("(")+1: hdr.rfind(")")]
                blocks.append((cond, (start_block, end_block)))
            elif hdr.startswith("elif"):
                cond = hdr[hdr.find("(")+1: hdr.rfind(")")]
                blocks.append((cond, (start_block, end_block)))
            elif hdr.startswith("else"):
                blocks.append((None, (start_block, end_block)))

        # Execute first matching
        for cond, (bs, be) in blocks:
            if cond is None or bool(self._eval(cond)):
                self._exec_block(lines, bs, be)
                break

        return headers[-1][0] + 1  # position after end

    def _handle_loop_count(self, lines: List[str], i: int, end: int, count_expr: str) -> int:
        # find matching end for this loop
        j = i + 1
        depth = 1
        while j < end and depth > 0:
            t = lines[j].strip()
            if re.match(r"^if\s*\(.+\):\s*$", t) or re.match(r"^loop\s*(\(|[A-Za-z_])", t) or re.match(r"^fn\s+[A-Za-z_]\w*\s*\([^)]*\):\s*$", t):
                depth += 1
            elif t == "end":
                depth -= 1
            j += 1
        count = int(self._eval(count_expr))
        for _ in range(count):
            self._exec_block(lines, i+1, j-1)
        return j

    def _handle_loop_each(self, lines: List[str], i: int, end: int, arr_name: str) -> int:
        j = i + 1
        depth = 1
        while j < end and depth > 0:
            t = lines[j].strip()
            if re.match(r"^if\s*\(.+\):\s*$", t) or re.match(r"^loop\s*(\(|[A-Za-z_])", t) or re.match(r"^fn\s+[A-Za-z_]\w*\s*\([^)]*\):\s*$", t):
                depth += 1
            elif t == "end":
                depth -= 1
            j += 1
        arr = self.vars.get(arr_name, [])
        for item in list(arr):
            self.vars["item"] = item
            self._exec_block(lines, i+1, j-1)
        self.vars.pop("item", None)
        return j
