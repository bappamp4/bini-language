BINI — Bhasha In Nano Instructions
BINI (Bhasha In Nano Instructions) is a compact assembly language and bytecode virtual machine designed for tiny AI systems and resource-constrained environments.
The idea is simple:
Natural language → BINI → compact bytecode → BINI VM
BINI provides a small instruction set for representing text, numbers, computation, control flow, and simple device-style operations in a compact deterministic format.
Why BINI?
BINI focuses on a small instruction set and compact bytecode.
For example:
PRINT hello
can become:
03 06 FF
where:
03 = PRINT word
06 = hello
FF = HALT
The BINI VM can execute the resulting bytecode directly.
BINI v1.1
Current version:
BINI v1.1
The project currently includes:
BINI virtual machine
BINI assembler
BINI disassembler
8 general-purpose registers (R0–R7)
16-bit register values
labels and jumps
conditional jumps
arithmetic
compact word-table strings
literal text output
GPIO instructions
timer instructions
fan instructions
built-in tests
command-line interface
Quick Start
Run the built-in tests:
python bini.py test
Run bytecode directly:
python bini.py hex "03 06 FF"
Assemble a BINI program:
python bini.py asm program.bini
Disassemble bytecode:
python bini.py dis "03 06 FF"
Trace execution:
python bini.py trace program.bini
Your First BINI Program
Create a file called:
hello.bini
Put:
print hello
halt
Then run:
python bini.py asm hello.bini
The program is assembled into compact bytecode and executed by the BINI VM.
Instruction Set
Opcode
Instruction
Purpose
01
PRINT literal
Print literal text
02
LOAD
Load a 16-bit value into a register
03
PRINT word
Print a word from the string table
04
GPIO
GPIO ON/OFF
05
TIMER
Timer operation
06
FAN
FAN ON/OFF
07
ADD
Add two registers
08
JMP
Unconditional jump
09
JZ
Jump if register is zero
0A
PRINT register
Print a register value
0B
SUB
Subtract two registers
FF
HALT
Stop execution
Examples
Print a word
print hello
halt
Bytecode:
03 06 FF
Load and print a number
load r1 7392
print r1
halt
GPIO
gpio on
halt
Bytecode:
04 01 FF
Fan
fan off
halt
Timer
timer 06:00
halt
Arithmetic
load r0 5
load r1 3
add r2 r0 r1
print r2
halt
Loop
BINI supports labels and conditional jumps:
load r0 3
load r1 1

loop:
print r0
sub r0 r0 r1
jz r0 end
jmp loop

end:
halt
This produces:
3
2
1
Bytecode
BINI programs are represented as bytes.
Example:
03 06 FF
The VM interprets the instructions sequentially.
BINI programs terminate with:
FF
Architecture
                Natural Language
                       │
                       ▼
                 Tiny AI / Learner
                       │
                       ▼
                      BINI
                       │
                       ▼
                  Bytecode
                       │
                       ▼
                    BINI VM
                       │
                       ▼
              Output / Device Action
The BINI language and VM form the deterministic execution layer.
A separate AI/learner can generate BINI programs from natural-language input.
Project Structure
bini-language/
│
├── bini.py
├── README.md
└── LICENSE
More examples, documentation, and learning components can be added as the project develops.
Status
BINI v1.1 — Public Experimental Release
BINI is an experimental language and VM project.
The instruction set and implementation may evolve in future versions.
License
BINI is released under the MIT License.
Author
Created as an experimental compact language and virtual machine for tiny AI systems.
BINI — Bhasha In Nano Instructions
