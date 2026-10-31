# Documentation

The builder generates seven sections from independent repository-owned Markdown:

- Getting Started: cwhip `doc/GETTING_STARTED.md` and `doc/FIRST-PROGRAM.md`.
- Language & Compiler: other cwhip `doc/` Markdown, excluding the obsolete integrated CEDIT and CDBG guides.
- Editor: cedit `CEDIT.md`, `README.md`, and `doc/`.
- Debugger: cdbg `CDBG.md`, `README.md`, and `doc/`.
- Macro Processor (cmacros): `cmacros/README.md`, `cmacros/doc/{BUILD,LANGUAGE,DIAGNOSTICS,USAGE,EXAMPLES}.md`, `cmacros/CHANGELOG.md`, and `cmacros/examples/README.md`, with raw example sources, expected outputs, license, and runner links.
- CVM: `cvm/README.md` and `cvm/doc/`.
- Parser Generator (cparsegen): `cparsegen/README.md` and `cparsegen/doc/`.

Sources stay in their repositories; only generated pages and referenced assets are copied.
Doxygen is optional, added manually later, and has no mandatory navigation link.
