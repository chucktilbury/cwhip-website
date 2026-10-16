# Documentation

The builder generates five sections from component-owned Markdown:

- Getting Started: workspace `doc/FIRST-PROGRAM.md`.
- Language & Compiler: `compiler/doc/`, excluding the obsolete integrated CEDIT and CDBG guides.
- Editor: `editor/CEDIT.md`, `editor/README.md`, and `editor/doc/`.
- Debugger: `debugger/CDBG.md`, `debugger/README.md`, and `debugger/doc/`.
- Contributor Workflow: the other workspace `doc/` documents.

Sources stay in their repositories; only generated pages and referenced assets are copied.
Doxygen is optional, added manually later, and has no mandatory navigation link.
