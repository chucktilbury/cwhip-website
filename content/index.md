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

- Signed 64-bit `int`, `unsigned`, `float`; string type is `strg`.
- Classes with inheritance.
- Managed strings and collections (`list`, `dict`).
- Exceptions and native bindings.

## Applications

Explore the [Editor](docs.html#editor), [Debugger](docs.html#debugger), and
[Macro Processor (cmacros)](docs.html#cmacros) documentation.
`cmacros` is a standalone command-line macro processor written in Cwhip,
not a compiler pipeline stage or GUI application. Its documentation includes
build instructions, the language contract, diagnostics, and original examples
with source files and an output-checking runner. Binary releases and icons
are deferred.

[Documentation](docs.html) · [About this site](about-site.html) · [GitHub](https://github.com/chucktilbury/cwhip)
