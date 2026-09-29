"""BINI v1.1 (Bhasha In Nano Instructions): VM, assembler, disassembler.

Usage:
  python bini.py hex "03 06 FF"     run a program written as hex bytes
  python bini.py asm prog.txt       assemble a file, show the bytes, run it
  python bini.py dis "03 06 FF"     turn bytes back into assembly
  python bini.py trace prog.txt     run step by step and watch the registers
  python bini.py test               run the self-tests
"""
import re
import sys

# The default string table. Both the program writer and the VM must share it.
WORDS = {4: "boss", 5: "tiny", 6: "hello", 7: "on", 8: "off", 9: "wifi", 10: "alarm"}


class BiniError(Exception):
    pass


# ---------------------------------------------------------------- reading hex
def parse_hex(text):
    """'03 06 FF' or '0306ff' -> bytes.  Anything after # on a line is ignored."""
    digits = re.sub(r"#.*", "", text)
    digits = re.sub(r"\s+", "", digits)
    if len(digits) % 2 or not re.fullmatch(r"[0-9a-fA-F]*", digits):
        raise BiniError("hex must be pairs of digits 0-9 A-F")
    return bytes.fromhex(digits)


# ------------------------------------------------------------------------ VM
def run(program, words=WORDS, max_steps=10_000, trace=None):
    """Run a BINI program. Returns the list of things it printed."""
    R = [0] * 8      # registers R0..R7, each holds 0..65535
    out = []         # everything the program prints
    pc = 0           # program counter: the byte we are reading now
    at = 0           # where the current instruction started
    steps = 0

    def fetch(n):    # read n operand bytes and move pc past them
        nonlocal pc
        if pc + n > len(program):
            raise BiniError(f"byte {at}: program ends in the middle of an instruction")
        chunk = program[pc:pc + n]
        pc += n
        return chunk

    def reg(i):
        if i > 7:
            raise BiniError(f"byte {at}: there is no register R{i} (use R0-R7)")
        return i

    def flag(v):
        if v > 1:
            raise BiniError(f"byte {at}: expected 00 or 01, got {v:02X}")
        return v

    def target(a):
        if a >= len(program):
            raise BiniError(f"byte {at}: jump to byte {a} is outside the program")
        return a

    while True:
        if pc >= len(program):
            raise BiniError("program ran off the end (every program must finish with FF)")
        steps += 1
        if steps > max_steps:
            raise BiniError(f"stopped after {max_steps} steps (infinite loop?)")
        at = pc
        op = program[pc]
        pc += 1

        if op == 0xFF:                                   # HALT
            if trace:
                trace(steps, at, R[:], len(out))
            break
        elif op == 0x01:                                 # PRINT text: 01 <ascii...> 00
            text = ""
            while True:
                c = fetch(1)[0]
                if c == 0:
                    break
                text += chr(c)
            out.append(text)
        elif op == 0x02:                                 # LOAD: 02 R HH LL
            r, hi, lo = fetch(3)
            R[reg(r)] = (hi << 8) | lo
        elif op == 0x03:                                 # PRINT word: 03 W
            w = fetch(1)[0]
            if w not in words:
                raise BiniError(f"byte {at}: word {w:02X} is not in the string table")
            out.append(words[w])
        elif op == 0x04:                                 # GPIO: 04 00/01
            out.append("GPIO ON" if flag(fetch(1)[0]) else "GPIO OFF")
        elif op == 0x05:                                 # TIMER: 05 HH MM
            hh, mm = fetch(2)
            if hh > 23 or mm > 59:
                raise BiniError(f"byte {at}: timer must be HH 0-23 and MM 0-59")
            out.append(f"TIMER {hh:02d}:{mm:02d}")
        elif op == 0x06:                                 # FAN: 06 00/01
            out.append("FAN ON" if flag(fetch(1)[0]) else "FAN OFF")
        elif op == 0x07:                                 # ADD: 07 D A B  (D = A + B)
            d, a, b = fetch(3)
            R[reg(d)] = (R[reg(a)] + R[reg(b)]) & 0xFFFF
        elif op == 0x08:                                 # JMP: 08 ADDR
            pc = target(fetch(1)[0])
        elif op == 0x09:                                 # JZ: 09 R ADDR (jump if R is 0)
            r, a = fetch(2)
            a = target(a)
            if R[reg(r)] == 0:
                pc = a
        elif op == 0x0A:                                 # PRINT register: 0A R
            out.append(str(R[reg(fetch(1)[0])]))
        elif op == 0x0B:                                 # SUB: 0B D A B  (D = A - B)
            d, a, b = fetch(3)
            R[reg(d)] = (R[reg(a)] - R[reg(b)]) & 0xFFFF
        else:
            raise BiniError(f"byte {at}: unknown instruction {op:02X}")

        if trace:
            trace(steps, at, R[:], len(out))
    return out


# --------------------------------------------------------------- disassembler
_FORMATS = {   # opcode: (operand bytes, how to show it)
    0x02: (3, lambda r, h, l, w: f"load r{r} {h << 8 | l}"),
    0x03: (1, lambda i, w: f"print {w.get(i, '?')}"),
    0x04: (1, lambda v, w: f"gpio {'on' if v else 'off'}"),
    0x05: (2, lambda h, m, w: f"timer {h:02d}:{m:02d}"),
    0x06: (1, lambda v, w: f"fan {'on' if v else 'off'}"),
    0x07: (3, lambda d, a, b, w: f"add r{d} r{a} r{b}"),
    0x08: (1, lambda a, w: f"jmp @{a}"),
    0x09: (2, lambda r, a, w: f"jz r{r} @{a}"),
    0x0A: (1, lambda r, w: f"print r{r}"),
    0x0B: (3, lambda d, a, b, w: f"sub r{d} r{a} r{b}"),
}


def disassemble(program, words=WORDS):
    """bytes -> list of (address, bytes, assembly text)."""
    rows, pc = [], 0
    while pc < len(program):
        at, op = pc, program[pc]
        pc += 1
        if op == 0xFF:
            text = "halt"
        elif op == 0x01:
            end = program.find(b"\x00", pc)
            if end < 0:
                rows.append((at, program[at:], "?? text never ends"))
                break
            text = 'print "' + program[pc:end].decode("latin-1") + '"'
            pc = end + 1
        elif op in _FORMATS:
            n, fmt = _FORMATS[op]
            if pc + n > len(program):
                rows.append((at, program[at:], "?? cut off"))
                break
            text = fmt(*program[pc:pc + n], words)
            pc += n
        else:
            text = f"?? unknown {op:02X}"
        rows.append((at, program[at:pc], text))
    return rows


# ------------------------------------------------------------------ assembler
_ARITY = {"print": 1, "load": 2, "gpio": 1, "fan": 1, "timer": 1,
          "add": 3, "sub": 3, "jmp": 1, "jz": 2, "halt": 0}


def _strip_comment(line):
    in_quote = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quote = not in_quote
        elif ch == "#" and not in_quote:
            return line[:i]
    return line


def _reg(tok):
    if not re.fullmatch(r"r[0-7]", tok):
        raise BiniError(f"'{tok}' is not a register (use r0-r7)")
    return int(tok[1])


def _num(tok, lo, hi):
    try:
        v = int(tok, 16) if tok.startswith("0x") else int(tok, 10)
    except ValueError:
        raise BiniError(f"'{tok}' is not a number") from None
    if not lo <= v <= hi:
        raise BiniError(f"{tok} is out of range ({lo} to {hi})")
    return v


def _onoff(tok):
    if tok not in ("on", "off"):
        raise BiniError(f"expected on or off, got '{tok}'")
    return 1 if tok == "on" else 0


def _addr(tok, labels, strict):
    if tok.startswith("@"):
        return _num(tok[1:], 0, 255)
    if tok in labels:
        return labels[tok]
    if strict:
        raise BiniError(f"unknown label '{tok}'")
    return 0        # first pass: we only need the size, not the address


def _encode(kind, arg, labels, strict, ids):
    if kind == "lit":
        if not all(0x20 <= ord(c) <= 0x7E for c in arg):
            raise BiniError("text may only use printable ASCII characters")
        return b"\x01" + arg.encode("ascii") + b"\x00"
    op, *a = arg
    if op not in _ARITY:
        raise BiniError(f"unknown instruction '{op}'")
    if len(a) != _ARITY[op]:
        raise BiniError(f"'{op}' needs {_ARITY[op]} value(s), got {len(a)}")
    if op == "halt":
        return b"\xff"
    if op == "print":
        if re.fullmatch(r"r\d+", a[0]):
            return bytes([0x0A, _reg(a[0])])
        if a[0] in ids:
            return bytes([0x03, ids[a[0]]])
        raise BiniError(f"'{a[0]}' is not in the string table "
                        f"(for custom text write print \"{a[0]}\")")
    if op == "load":
        v = _num(a[1], 0, 65535)
        return bytes([0x02, _reg(a[0]), v >> 8, v & 0xFF])
    if op == "gpio":
        return bytes([0x04, _onoff(a[0])])
    if op == "fan":
        return bytes([0x06, _onoff(a[0])])
    if op == "timer":
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", a[0])
        if not m or int(m[1]) > 23 or int(m[2]) > 59:
            raise BiniError("timer must look like HH:MM (hours 0-23, minutes 0-59)")
        return bytes([0x05, int(m[1]), int(m[2])])
    if op in ("add", "sub"):
        code = 0x07 if op == "add" else 0x0B
        return bytes([code, _reg(a[0]), _reg(a[1]), _reg(a[2])])
    if op == "jmp":
        return bytes([0x08, _addr(a[0], labels, strict)])
    return bytes([0x09, _reg(a[0]), _addr(a[1], labels, strict)])      # jz


def assemble(source, words=WORDS):
    """Assembly text -> bytes. A final FF (halt) is added if you forget it."""
    ids = {w: i for i, w in words.items()}
    items = []                                   # (line number, kind, argument)
    for n, raw in enumerate(source.splitlines(), 1):
        line = _strip_comment(raw).strip()
        while (m := re.match(r"([A-Za-z_]\w*):\s*(.*)$", line)):
            items.append((n, "label", m.group(1).lower()))
            line = m.group(2)
        if not line:
            continue
        m = re.fullmatch(r'(?i)print\s+"(.*)"', line)
        if m:
            items.append((n, "lit", m.group(1)))
        else:
            items.append((n, "ins", line.lower().split()))
    if not items or items[-1][1:] != ("ins", ["halt"]):
        items.append((0, "ins", ["halt"]))

    def emit(n, kind, arg, labels, strict):
        try:
            return _encode(kind, arg, labels, strict, ids)
        except BiniError as e:
            raise BiniError(f"line {n}: {e}") from None

    labels, pc = {}, 0                           # pass 1: find every label's address
    for n, kind, arg in items:
        if kind == "label":
            if arg in labels:
                raise BiniError(f"line {n}: label '{arg}' is defined twice")
            labels[arg] = pc
        else:
            pc += len(emit(n, kind, arg, {}, False))
    if pc > 255:
        raise BiniError(f"program is {pc} bytes; the limit is 255")
    return b"".join(emit(n, k, a, labels, True) for n, k, a in items if k != "label")


# ------------------------------------------------------------------ self-test
def selftest():
    def hexrun(h):
        return run(parse_hex(h))

    def fails(fn, *args):
        try:
            fn(*args)
        except BiniError:
            return True
        return False

    assert hexrun("03 06 FF") == ["hello"]
    assert hexrun("03 08 FF") == ["off"]                       # v1.0 crashed here
    assert hexrun("03 06 03 04 FF") == ["hello", "boss"]
    assert hexrun("02 01 1C E0 0A 01 FF") == ["7392"]
    assert hexrun("02 05 00 2A 0A 05 03 05 FF") == ["42", "tiny"]   # R5 vs word 05
    assert hexrun("01 74 69 6E 79 00 FF") == ["tiny"]
    assert hexrun("04 01 FF") == ["GPIO ON"]
    assert hexrun("06 00 FF") == ["FAN OFF"]
    assert hexrun("05 06 00 FF") == ["TIMER 06:00"]
    assert hexrun("02 00 00 05 02 01 00 03 07 02 00 01 0A 02 FF") == ["8"]
    assert hexrun("02 00 FF FF 02 01 00 01 07 02 00 01 0A 02 FF") == ["0"]      # wraps
    assert hexrun("02 00 00 00 02 01 00 01 0B 02 00 01 0A 02 FF") == ["65535"]  # wraps
    countdown = assemble("load r0 3\nload r1 1\nloop:\nprint r0\nsub r0 r0 r1\n"
                         "jz r0 end\njmp loop\nend:\nhalt")
    assert run(countdown) == ["3", "2", "1"]
    assert assemble("print hello") == bytes.fromhex("0306FF")
    assert assemble('print "Hi"') == bytes.fromhex("014869" "00FF")
    assert [t for _, _, t in disassemble(countdown)][0] == "load r0 3"
    assert assemble("\n".join(t for _, _, t in disassemble(countdown))) == countdown
    for bad in ("0C FF", "04", "03 06", "08 00", "04 02 FF", "02 08 00 01 FF", "08 09 FF"):
        assert fails(hexrun, bad), bad
    for bad in ("gpio onn", "print r9", "jmp nowhere", "print bananas", "fan", "load r0 70000"):
        assert fails(assemble, bad), bad
    custom = {**WORDS, 11: "door"}
    assert run(assemble("print door", custom), custom) == ["door"]


# ------------------------------------------------------------------------ CLI
def main(argv):
    if len(argv) < 2 or argv[1] not in ("hex", "asm", "dis", "trace", "test"):
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd != "test" and len(argv) < 3:
        print(__doc__)
        return 1
    try:
        if cmd == "test":
            selftest()
            print("all tests passed")
            return 0
        if cmd in ("hex", "dis"):
            program = parse_hex(" ".join(argv[2:]))
        else:
            with open(argv[2]) as f:
                program = assemble(f.read())
            print(f"assembled {len(program)} bytes: " + " ".join(f"{b:02X}" for b in program))
        if cmd == "dis":
            for at, chunk, text in disassemble(program):
                print(f"{at:3d}  {' '.join(f'{b:02X}' for b in chunk):<14}{text}")
        elif cmd == "trace":
            names = {at: text for at, _, text in disassemble(program)}
            def show(step, at, regs, n_out):
                held = " ".join(f"r{i}={v}" for i, v in enumerate(regs) if v)
                print(f"step {step:3d}  byte {at:3d}  {names[at]:<18} {held}")
            for line in run(program, trace=show):
                print("  prints:", line)
        else:
            for line in run(program):
                print(line)
    except (BiniError, OSError) as e:
        print("error:", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
