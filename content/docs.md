# Documentation

The builder generates six sections from component-owned Markdown:

- Getting Started: cwhip repository `doc/GETTING_STARTED.md` (workspace `compiler/doc/GETTING_STARTED.md`) and workspace `doc/FIRST-PROGRAM.md`.
- Language & Compiler: `compiler/doc/`, excluding the obsolete integrated CEDIT and CDBG guides.
- Editor: `editor/CEDIT.md`, `editor/README.md`, and `editor/doc/`.
- Debugger: `debugger/CDBG.md`, `debugger/README.md`, and `debugger/doc/`.
- Macro Processor (cmacros): `cmacros/README.md`, `cmacros/doc/{BUILD,LANGUAGE,DIAGNOSTICS}.md`, and `cmacros/examples/README.md`, with raw example sources, expected outputs, license, and runner links.
- Contributor Workflow: the other workspace `doc/` documents.

Sources stay in their repositories; only generated pages and referenced assets are copied.
Doxygen is optional, added manually later, and has no mandatory navigation link.
