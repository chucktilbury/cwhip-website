# cwhip-website

`cwhip-website` is the source for [cwhip.org](https://cwhip.org). It imports
Markdown from sibling component repositories at build time; documentation is
not copied into this tree. Source:
[github.com/chucktilbury/cwhip-website](https://github.com/chucktilbury/cwhip-website).

This directory contains the builder in `build.py`, site chrome in `content/`,
and tests in `tests/`. Generated HTML lands in `site/`. Python 3.9+ and its
standard library are enough; there is no package install step.

With sibling checkouts of `cwhip`, `cedit`, `cdbg`, `cmacros`, `cvm`, and
`cparsegen` next to this repository, build and check the site:

```sh
python3 /path/to/projects/cwhip-website/build.py
python3 /path/to/projects/cwhip-website/check_site.py /path/to/projects/cwhip-website/site
```

```text
projects/
  cwhip-website/
  cwhip/
  cedit/
  cdbg/
  cmacros/
  cvm/
  cparsegen/
```

- [Documentation index (generated)](content/docs.md)
- [About this site](content/about-site.md)

By default, discovery uses the parent of `build.py`, not the caller's working
directory. For siblings elsewhere, use `--repos-root`:

```sh
python3 build.py --repos-root /path/to/projects --output-dir /tmp/cwhip-site
python3 check_site.py /tmp/cwhip-site
```

For checkouts in separate locations, override any or all repository roots.
Unspecified roots still use `--repos-root`, or the website's parent directory:

```sh
python3 build.py \
  --cwhip-root /src/language \
  --cedit-root /src/tools/editor \
  --cdbg-root /src/tools/debugger \
  --cmacros-root /src/macros \
  --cvm-root /src/vm \
  --cparsegen-root /src/parsergen \
  --output-dir /tmp/cwhip-site
```

`--output-dir` defaults to `site/` beside `build.py`. The builder reads sources
without changing them and never clones, fetches, installs, or uploads anything.
Use current component checkouts. A missing required checkout or guide fails with
its path before output is written. During the upstream first-program guide
migration, missing cwhip `doc/FIRST-PROGRAM.md` emits an explicit warning and
omits only that page; update the compiler checkout to publish it automatically.
`doc/GETTING_STARTED.md` remains required for full builds.
No combined repository or submodule layout is needed.

| Section | Canonical sources | Output |
| --- | --- | --- |
| Getting Started | cwhip `doc/GETTING_STARTED.md`, `doc/FIRST-PROGRAM.md` | `getting-started/` |
| Language & Compiler | other cwhip `doc/**/*.md` | `compiler/` |
| Editor | cedit `CEDIT.md`, optional `README.md`, `doc/**/*.md` | `editor/` |
| Debugger | cdbg `CDBG.md`, optional `README.md`, `doc/**/*.md` | `debugger/` |
| Macro Processor (cmacros) | cmacros `README.md`, `doc/{BUILD,LANGUAGE,DIAGNOSTICS,USAGE,EXAMPLES}.md`, `CHANGELOG.md`, `examples/README.md` | `cmacros/` |
| CVM | cvm `README.md`, `doc/**/*.md` | `cvm/` |
| Parser Generator (cparsegen) | cparsegen `README.md`, `doc/**/*.md` | `cparsegen/` |

The compiler section keeps the original core-document order, followed by other
documents. Obsolete cwhip `doc/CEDIT.md` and `doc/CDBG.md` are not published;
links to them resolve to the authoritative component guides. The old embedded
`doc/website/` subtree is excluded. There is no contributor-workflow section.

Recognized relative links between imported documents become relative HTML links,
including fragments. Referenced non-Markdown assets are copied into `assets/`
under stable component prefixes (`compiler`, `editor`, `debugger`, `cmacros`,
`cvm`, `cparsegen`), independent of the checkout directories' names. Links to
other existing repository Markdown outside the documentation inputs (for example
cwhip `stdlib/README.md`) become external GitHub links using the compiler's
`master` branch and the other repositories' `main` branches. External pages are
not recursively imported or checked over the network.

Inline/fenced code examples are not treated as links. Link labels may contain
inline code or emphasis; their destinations are rewritten like plain-text links.
The homepage's syntax overview is maintained here; component-owned examples and
syntax prose must be corrected in their source repositories, not during import.
Fenced code is HTML-escaped and otherwise preserved; `content/app.js` does not
implement syntax highlighting or maintain a keyword list.

Recognized local links, heading fragments, navigation, scripts, stylesheets and
images are checked during every build. Missing required sources or invalid
recognized local links fail with an explicit error. The checker does not verify
documentation claims, external URLs, or links that failed to render as anchors.
Compatibility redirects retain old flat compiler-document URLs and fragments,
including `CEDIT.html`/`CDBG.html` redirects to component sections in full builds.

All listed cmacros guides are required for a full build. Its examples guide
gains a generated file listing: the runner, upstream license, original `.txt`
inputs, and expected `.out` files are copied byte-for-byte to
`assets/cmacros/examples/`, never parsed as Markdown or executed. The runner and
license are required inputs. Canonical provenance links stay external;
directories without a README link to their repository tree. Each cmacros guide
links back to its canonical GitHub source. The CLI is standalone, not integrated
into the compiler pipeline. Full builds also require `cvm/README.md` plus at
least one `cvm/doc/*.md`, and the same for `cparsegen`.

Generated filenames are recorded in `site/.generated-files.json`; subsequent
builds remove only previously recorded stale files, including workflow pages from
older builds. Unmanaged files are not removed. Doxygen is **not required**,
generated, or linked by default. You may add its output manually under
`site/html/`; rebuilding preserves it.

## Partial compiler-only build

```sh
python3 build.py --docs-dir /path/to/cwhip/doc --output-dir /tmp/cwhip-site
```

This deliberately partial site requires only compiler Markdown. Unavailable
sections say that a full build from standalone repositories is required, rather
than publishing broken links. Application links in compiler documents point to
the authoritative guides on GitHub. Do not combine `--docs-dir` with repository
root options.

`build.py` declares `BUILDER_API = 4`. Callers should invoke the standalone CLI
with the roots above and keep output outside source trees. The former combined
layout input and implicit legacy `doc/website/` staging fallback are no longer
supported.

## Checks and publication

```sh
python3 -m unittest discover -s tests -v
```

Tests cover complete/partial builds, default sibling discovery, explicit roots,
arbitrary working directories, paths with spaces, independent component sections,
authoritative guide links, assets, missing inputs, fragments, Markdown rendering,
current homepage syntax guidance, verbatim Cwhip samples, and stale-file cleanup.
To validate output independently, run `python3 check_site.py /path/to/site`.

Publication remains manual. This repository has no `install.sh` or upload
command. The compiler's legacy `doc/website/install.sh` is a historical upload
script, not a build or validation command; do not run it to preview this site.
A local build does not update or verify the public site. Review generated output
and separately check published pages before treating live documentation as current.
