# Cwhip

A statically typed language with classes, inheritance, managed strings and collections, exceptions, and native bindings.

The compiler frontend is written in C++17; the runtime is in C. Source files use the `.cw` extension. The compiler command is `cwhip`.

[Go to working areas](https://github.com/chucktilbury/cwhip-workspace/wiki)  
*(placeholder destination — discussions, announcements, or other non-documentation tasks)*

## Quick start

1. Clone the repository and build with CMake.
2. Compile a program: `./bin/cwhip path/to/program.cw -o build/program`
3. Run it: `./build/program`

Start with the [Getting Started documentation](docs.html#getting-started), or browse the documentation for installation details and the language reference.

## Language highlights

- Fixed-width integers `int8`/`uint8` through `int64`/`uint64`, and floating-point types `fp32`/`fp64`; string type is `strg`.
- Classes with inheritance.
- Managed strings and collections (`list`, `dict`).
- Exceptions and native bindings.

The current SDK is **0.0.2**, with ABI **numeric-v2**. The former numeric
names `int`, `unsigned`, and `float` are reserved and rejected, not aliases.
FP8, FP16, and BF16 are deferred. See the numeric migration guide in the
[Language & Compiler documentation](docs.html#compiler) before upgrading
existing programs or native packages.

## Applications

Explore the [Editor](docs.html#editor), [Debugger](docs.html#debugger), and
[Macro Processor (cmacros)](docs.html#cmacros) documentation.
`cmacros` is a standalone command-line macro processor written in Cwhip,
not a compiler pipeline stage or GUI application. Its documentation includes
build instructions, the language contract, diagnostics, and original examples
with source files and an output-checking runner. Binary releases and icons
are deferred.

[Documentation](docs.html) · [About this site](about-site.html) · [GitHub](https://github.com/chucktilbury/cwhip)
