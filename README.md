# Cwhip website

Source for [cwhip.org](https://cwhip.org). The existing design, stylesheet, home
page, and component-owned documentation are preserved. Requires Python 3.9+
and its standard library only; no package installation is needed.

## Build from a workspace

From any directory:

```sh
python3 /path/to/website/build.py \
  --workspace /path/to/cwhip-workspace \
  --output-dir /path/to/build/website/site
python3 /path/to/website/check_site.py /path/to/build/website/site
```

`--output-dir` defaults to `site/` beside `build.py`, not the caller's directory.
The builder reads sources without changing them. There are no maintained copies
of component documentation here. The generated index has these sections:

| Section | Canonical sources | Output |
| --- | --- | --- |
| Getting Started | cwhip `doc/GETTING_STARTED.md` (workspace `compiler/doc/GETTING_STARTED.md`), workspace `doc/FIRST-PROGRAM.md` | `getting-started/` |
| Language & Compiler | `compiler/doc/**/*.md` | `compiler/` |
| Editor | `editor/CEDIT.md`, `editor/README.md`, `editor/doc/**/*.md` | `editor/` |
| Debugger | `debugger/CDBG.md`, `debugger/README.md`, `debugger/doc/**/*.md` | `debugger/` |
| Macro Processor (cmacros) | `cmacros/README.md`, `cmacros/doc/{BUILD,LANGUAGE,DIAGNOSTICS}.md`, `cmacros/examples/README.md` | `cmacros/` |
| Contributor Workflow | other workspace `doc/**/*.md` | `workflow/` |

The compiler section keeps the original core-document order, followed by other
documents. Obsolete `compiler/doc/CEDIT.md` and `CDBG.md` are not published;
links to them resolve to the authoritative component guides. The old embedded
`compiler/doc/website/` subtree is excluded.

Recognized relative links between imported documents become relative HTML links,
including fragments. Referenced non-Markdown assets are copied into `assets/`.
Links to other existing repository Markdown outside these documentation inputs
(for example `compiler/stdlib/README.md`) are generated as external GitHub links
using the compiler's `master` branch and the other repositories' `main` branches;
those external pages are not recursively imported or checked over the network.

Inline/fenced code examples are not treated as links. Link labels may contain
inline code or emphasis; their destinations are rewritten like plain-text links.

Recognized local links, heading fragments, navigation, scripts, stylesheets and
images are checked during every build. Missing required sources or invalid
recognized local links fail with an explicit error. The checker does not verify
documentation claims, external URLs, or links that failed to render as anchors.
Compatibility redirects retain the old flat compiler-document URLs and their
fragments, including redirects from `CEDIT.html`/`CDBG.html` to their component
sections in full workspace builds.

The cmacros checkout is a peer at workspace-root `cmacros/`, mapped to
[`chucktilbury/cmacros`](https://github.com/chucktilbury/cmacros). All five
listed guides are required for a full workspace build; a missing checkout or
guide fails explicitly. Its examples guide gains a generated file listing:
the runner, upstream license, original `.txt` inputs, and expected `.out`
files are copied byte-for-byte to `assets/cmacros/examples/`, never parsed as
Markdown or executed. The runner and license are required inputs. Canonical
provenance links stay external; directories without a README link to their
repository tree. Each cmacros guide links back to its canonical GitHub source.
The CLI is standalone, not integrated into the compiler pipeline.

Generated filenames are recorded in `site/.generated-files.json`; subsequent
builds remove only previously recorded stale files. Unmanaged files are not
removed. Doxygen is **not required**, generated, or linked by default. You may
add its output manually under `site/html/`; rebuilding preserves it.

## Partial compiler-only build and legacy staging

```sh
python3 build.py --docs-dir /path/to/compiler/doc --output-dir /tmp/cwhip-site
```

This builds a deliberately partial site: unavailable sections say that a full
workspace is required rather than publishing broken links. Application links
in compiler documents point to the authoritative guides on GitHub. Without an
explicit input, the only supported fallback is the old workspace adapter's
`doc/website/` staging layout, detected by a parent `INSTALLATION.md`.
An ordinary standalone checkout with no documentation input fails.

## Workspace integration contract

`build.py` declares `BUILDER_API = 2`. An adapter using this capability should
invoke the builder with `--workspace ROOT --output-dir OUTPUT` and keep OUTPUT
outside documentation source directories. It can invoke this checkout directly:
no source staging is necessary. If staging the website instead, include
`build.py`, **`check_site.py`**, and `content/`. The old adapter that copies only
`build.py` is not sufficient for this revision.

The workspace owns its CMake target and adapter. Its current adapter invokes
the pinned builder in full-workspace mode, and its registered `cmacros/`
submodule and pinned website revision already support the cmacros section.
Updating this checkout does not update a workspace submodule pin: adopting
subsequent website fixes still requires a separate workspace pin update.

Full-workspace builds import the component revisions actually checked out; they
do not fetch upstream heads or advance submodule pins. The workspace's committed
component pins may predate the numeric-v2 migration even when upstream component
repositories contain it. A build using current upstream source archives is
therefore distinct from an exact-pinned workspace build. Check component
revisions before assuming imported guides match the current SDK described on
the home page.

For older workspace revisions, register and populate the `cmacros/` submodule
and use an adapter supporting full-workspace input before adopting this builder.
The compiler-only/legacy staging interface and `BUILDER_API = 2` remain
available; partial builds show the cmacros section as unavailable without linking
to missing generated pages.

## Checks and publication

```sh
python3 -m unittest discover -s tests -v
```

Tests cover complete/partial builds, arbitrary working directories, paths with
spaces, independent component sections, authoritative guide links, assets,
missing inputs, fragments, Markdown rendering, and stale-file cleanup.

Publication remains manual. This standalone repository does not contain an
`install.sh` or another upload command. The compiler's legacy
`doc/website/install.sh` is a separate historical upload script, not a build or
validation command; do not run it to preview this site. The builder never uploads
anything.

A local build does not update or verify the public site. Review generated output
and separately check published pages before treating the live documentation as
current.
