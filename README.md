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
| Contributor Workflow | other workspace `doc/**/*.md` | `workflow/` |

The compiler section keeps the original core-document order, followed by other
documents. Obsolete `compiler/doc/CEDIT.md` and `CDBG.md` are not published;
links to them resolve to the authoritative component guides. The old embedded
`compiler/doc/website/` subtree is excluded.

Relative links between imported documents become relative HTML links, including
fragments. Referenced non-Markdown assets are copied into `assets/`. Links to
other existing repository Markdown outside these documentation inputs (for
example `compiler/stdlib/README.md`) go to that repository on GitHub `main`;
those external pages are not recursively imported or checked over the network.
Inline/fenced code examples are not treated as links. Local links, heading
fragments, navigation, scripts, stylesheets and images are checked during every
build. Missing required sources or invalid links fail with an explicit error.
Compatibility redirects retain the old flat compiler-document URLs and their
fragments, including redirects from `CEDIT.html`/`CDBG.html` to their component
sections in full workspace builds.

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

The workspace owns its CMake target and adapter, including backward compatibility
with its pinned older generator. Updating this checkout does not update a
workspace submodule pin. A published/versioned website revision and a workspace
integration update are needed before the pinned normal target uses the new
sections.

## Checks and publication

```sh
python3 -m unittest discover -s tests -v
```

Tests cover complete/partial builds, arbitrary working directories, paths with
spaces, independent component sections, authoritative guide links, assets,
missing inputs, fragments, Markdown rendering, and stale-file cleanup.

Publication remains manual. `install.sh` is the pre-existing upload command,
not a build or validation command; do not run it to preview the site. The
builder never uploads anything.
