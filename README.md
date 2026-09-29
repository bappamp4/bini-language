# BINI — Bhasha In Nano Instructions
BINI (Bhasha In Nano Instructions) is a compact assembly language and bytecode virtual machine designed for tiny AI systems and resource-constrained environments.
The idea is simple:
**Natural language → BINI → compact bytecode → BINI VM → Output / Device Action**
BINI provides a small instruction set for representing text, numbers, computation, control flow, and simple device-style operations in a compact deterministic format.
## Why BINI?
BINI focuses on:
- A small instruction set
- Compact bytecode
- Deterministic execution
- A lightweight virtual machine
- Tiny AI and resource-constrained environments
- Simple device-style operations
For example:
```text
print hello
halt
```
can become:
```text
03 06 FF
```
where:
- `03` = PRINT word
- `06` = hello
- `FF` = HALT
The BINI VM can execute the resulting bytecode directly.
## Current Version
**BINI v1.1 — Public Experimental Release** ## Features
- BINI virtual machine
- BINI assembler
- BINI disassembler
- 8 general-purpose registers (`R0–R7`)
- 16-bit register values
- Labels and jumps
- Conditional jumps
- Arithmetic
- Compact word-table strings
- Literal text output
- GPIO instructions
- Timer instructions
- Fan instructions
- Built-in tests
- Command-line interface
## Quick Start
Run the built-in tests:
```bash
python bini.py test
```
Run bytecode directly:
```bash
python bini.py hex "03 06 FF"
```
Assemble a BINI program:
```bash
python bini.py asm program.bini
```
Disassemble bytecode:
```bash
python bini.py dis "03 06 FF"
``` Trace execution:
```bash
python bini.py trace program.bini
```
## Your First BINI Program
Create a file called `hello.bini`:
```text
print hello
halt
```
Then run:
```bash
python bini.py asm hello.bini
```
The program is assembled into compact bytecode and executed by the BINI VM.
## Instruction Set
| Opcode | Instruction | Purpose |
|---|---|---|
| `01` | PRINT literal | Print literal text |
| `02` | LOAD | Load a 16-bit value into a register |
| `03` | PRINT word | Print a word from the string table |
| `04` | GPIO | GPIO ON/OFF |
| `05` | TIMER | Timer operation |
| `06` | FAN | FAN ON/OFF |
| `07` | ADD | Add two registers |
| `08` | JMP | Unconditional jump |
| `09` | JZ | Jump if register is zero |
| `0A` | PRINT register | Print a register value |
| `0B` | SUB | Subtract two registers |
| `FF` | HALT | Stop execution |
## Examples
### Print a word
```text print hello
halt
```
### Arithmetic
```text
load r0 5
load r1 3
add r2 r0 r1
print r2
halt
```
### GPIO
```text
gpio on
halt
```
### Timer
```text
timer 06:00
halt
```
### Countdown
```text
load r0 3
load r1 1
loop:
print r0
sub r0 r0 r1
jz r0 end
jmp loop
end:
halt
```
## Architecture ```text
Natural Language
 ↓
 Tiny AI / Learner
 ↓
 BINI
 ↓
 Bytecode
 ↓
 BINI VM
 ↓
Output / Device Action
```
## Project Structure
```text
bini-language/
■■■ bini.py
■■■ examples/
■ ■■■ hello.bini
■ ■■■ arithmetic.bini
■ ■■■ gpio.bini
■ ■■■ timer.bini
■ ■■■ countdown.bini
■■■ README.md
■■■ LICENSE
```
## Status
**BINI v1.1 — Public Experimental Release**
BINI is an experimental project and will continue to evolve.
## License
Released under the MIT License.
## Author
BINI — Bhasha In Nano Instructions.
