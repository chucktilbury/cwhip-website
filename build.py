#!/usr/bin/env python3
"""Build cwhip.org from component-owned documentation; Python standard library only."""

import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

from check_site import check_site


ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
BUILDER_API = 2
SECTIONS = (
    ("getting-started", "Getting Started"),
    ("compiler", "Language & Compiler"),
    ("editor", "Editor"),
    ("debugger", "Debugger"),
    ("cmacros", "Macro Processor (cmacros)"),
    ("workflow", "Contributor Workflow"),
)
LINK = re.compile(r'(!?)\[([^\]]*)\]\(([^)\n]+)\)')


def heading_id(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def inline(text):
    # Protect code spans from emphasis/link interpretation.
    parts = re.split(r"(`[^`]+`)", text)
    for i, part in enumerate(parts):
        if part.startswith("`") and part.endswith("`"):
            parts[i] = "<code>" + html.escape(part[1:-1]) + "</code>"
            continue
        escaped = html.escape(part)
        escaped = LINK.sub(
            lambda m: (f'<img src="{m[3]}" alt="{m[2]}">' if m[1]
                       else f'<a href="{m[3]}">{m[2]}</a>'), escaped)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        parts[i] = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return "".join(parts)


def headings(text):
    """Share heading IDs between rendered pages and the documentation index."""
    counts = {}
    fenced = False
    result = []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match and not fenced:
            title = match[2]
            base = heading_id(title)
            count = counts.get(base, 0)
            counts[base] = count + 1
            result.append((len(match[1]), title, base + (f"-{count}" if count else "")))
    return result


def md_to_html(text):
    out, para, lists, rows = [], [], [], []
    ids = iter(headings(text))
    fenced = False

    def flush_para():
        if para:
            out.append("<p>" + "\n".join(inline(p) for p in para) + "</p>")
            para.clear()

    def close_lists(min_indent=-1):
        while lists and lists[-1][0] >= min_indent:
            _, tag = lists.pop()
            out.append(f"</li></{tag}>")

    def flush_table():
        if rows:
            out.append("<table>")
            for i, row in enumerate(rows):
                tag = "th" if i == 0 else "td"
                cells = re.split(r"(?<!\\)\|", row.strip().strip("|"))
                out.append("<tr>" + "".join(
                    f"<{tag}>{inline(c.strip().replace(chr(92) + '|', '|'))}</{tag}>"
                    for c in cells) + "</tr>")
            out.append("</table>")
            rows.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para()
            flush_table()
            close_lists()
            out.append("</code></pre>" if fenced else "<pre><code>")
            fenced = not fenced
            continue
        if fenced:
            out.append(html.escape(line))
            continue
        if not stripped:
            flush_para()
            flush_table()
            continue
        if stripped.startswith("|"):
            flush_para()
            close_lists()
            if not re.fullmatch(r"\|?[\s:|\-]+\|?", stripped):
                rows.append(stripped)
            continue
        flush_table()
        heading = re.match(r"^#{1,6}\s+", line)
        item = re.match(r"^(\s*)([-*]|\d+\.)\s+(.+)", line)
        if heading:
            flush_para()
            close_lists()
            level, title, anchor = next(ids)
            out.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
        elif item:
            flush_para()
            indent = len(item[1])
            tag = "ul" if item[2] in ("-", "*") else "ol"
            while lists and lists[-1][0] > indent:
                close_lists(lists[-1][0])
            if lists and lists[-1] == (indent, tag):
                out.append("</li><li>" + inline(item[3]))
            else:
                if lists and lists[-1][0] == indent:
                    close_lists(indent)
                out.append(f"<{tag}><li>{inline(item[3])}")
                lists.append((indent, tag))
        elif lists and line[:1].isspace():
            out.append(inline(stripped))
        else:
            close_lists()
            para.append(line)
    flush_para()
    flush_table()
    close_lists()
    if fenced:
        out.append("</code></pre>")
    return "\n".join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{root}styles.css">
</head>
<body>
<header class="top">
  <a class="logo" href="{root}index.html">cwhip</a>
  <nav class="main-nav">
    <a href="{root}index.html">Home</a>
    <a href="{root}docs.html#getting-started">Getting Started</a>
    <a href="{root}docs.html">Documentation</a>
    <a href="{root}about-site.html">About this site</a>
    <a href="https://github.com/chucktilbury/cwhip-workspace">GitHub</a>
  </nav>
</header>
<main>
{body}
</main>
<footer>
  <p>Cwhip. Documentation source of truth is the repository.</p>
</footer>
<script src="{root}app.js"></script>
</body>
</html>
"""


def relative(target, page):
    return Path(os.path.relpath(target, page.parent)).as_posix()


def build(workspace=None, docs_dir=None, output_dir=None):
    workspace = Path(workspace).resolve() if workspace else None
    docs_dir = Path(docs_dir).resolve() if docs_dir else None
    output = Path(output_dir).resolve() if output_dir else ROOT / "site"
    if workspace and docs_dir:
        raise ValueError("Use --workspace or --docs-dir, not both")
    if not workspace and not docs_dir:
        # Compatibility with the pinned workspace adapter's doc/website staging.
        if (ROOT.parent / "INSTALLATION.md").is_file():
            docs_dir = ROOT.parent
        else:
            raise ValueError("Documentation input required: use --workspace ROOT or --docs-dir DIR")
    sources = {}
    sections = {key: [] for key, _ in SECTIONS}
    aliases = {}
    assets = {}
    source_roots = [CONTENT]

    def add(source, destination, section=None):
        source = source.resolve()
        if source not in sources:
            sources[source] = Path(destination)
            if section:
                sections[section].append(source)

    for page in sorted(CONTENT.glob("*.md")):
        if page.name != "docs.md":
            add(page, page.with_suffix(".html").name)

    compiler_doc = workspace / "compiler/doc" if workspace else docs_dir
    if not compiler_doc.is_dir() or not list(compiler_doc.glob("*.md")):
        raise ValueError(f"No compiler documentation found in {compiler_doc}")
    getting_started = compiler_doc / "GETTING_STARTED.md"
    if workspace and not getting_started.is_file():
        raise ValueError(f"Required getting-started guide missing: {getting_started}")
    source_roots.append(compiler_doc.parent)
    compiler_order = [
        "INSTALLATION.md", "LANGUAGE-REFERENCE.md", "STDLIB.md", "PACKAGES.md",
        "EXAMPLES.md", "GTK.md", "DEBUGGING.md", "GRAMMAR.md",
    ]
    for page in sorted(compiler_doc.rglob("*.md"), key=lambda p: (
            compiler_order.index(p.name) if p.name in compiler_order else len(compiler_order),
            p.as_posix())):
        if "website" in page.relative_to(compiler_doc).parts:
            continue
        if page.name not in ("CEDIT.md", "CDBG.md") and (
                not workspace or page != getting_started):
            add(page, Path("compiler") / page.relative_to(compiler_doc).with_suffix(".html"), "compiler")
    if workspace:
        source_roots = [CONTENT, workspace]
        for component, guide in (("editor", "CEDIT.md"), ("debugger", "CDBG.md")):
            root = workspace / component
            if not (root / guide).is_file():
                raise ValueError(f"Required component guide missing: {root / guide}")
            pages = [root / guide]
            if (root / "README.md").is_file():
                pages.append(root / "README.md")
            pages += sorted((root / "doc").rglob("*.md"))
            for page in pages:
                add(page, Path(component) / page.relative_to(root).with_suffix(".html"), component)
            aliases[(compiler_doc / guide).resolve()] = (root / guide).resolve()
        macro_root = workspace / "cmacros"
        macro_pages = ["README.md", "doc/BUILD.md", "doc/LANGUAGE.md",
                       "doc/DIAGNOSTICS.md", "examples/README.md"]
        for name in macro_pages:
            source = macro_root / name
            if not source.is_file():
                raise ValueError(f"Required cmacros documentation missing: {source}")
            add(source, Path("cmacros") / Path(name).with_suffix(".html"), "cmacros")
        first = workspace / "doc/FIRST-PROGRAM.md"
        if not first.is_file():
            raise ValueError(f"Required first-program guide missing: {first}")
        add(getting_started, "getting-started/index.html", "getting-started")
        add(first, "getting-started/FIRST-PROGRAM.html", "getting-started")
        for page in sorted((workspace / "doc").rglob("*.md")):
            if page not in (first, getting_started):
                add(page, Path("workflow") / page.relative_to(workspace / "doc").with_suffix(".html"), "workflow")
    else:
        # A compiler-only build must not publish obsolete integrated application guides.
        for guide, component in (("CEDIT.md", "editor"), ("CDBG.md", "debugger")):
            aliases[(compiler_doc / guide).resolve()] = f"https://github.com/chucktilbury/{'cedit' if component == 'editor' else 'cdbg'}/blob/main/{guide}"

    def allowed(path):
        return any(path == root or root in path.parents for root in source_roots)

    def repository_link(source):
        roots = (
            [(workspace / component, repo) for component, repo in
             (("compiler", "cwhip"), ("editor", "cedit"), ("debugger", "cdbg"),
              ("cmacros", "cmacros"))]
            + [(workspace, "cwhip-workspace")] if workspace else
            [(compiler_doc.parent, "cwhip")]
        )
        for root, repo in roots:
            if root in source.parents:
                kind = "tree" if source.is_dir() else "blob"
                return (f"https://github.com/chucktilbury/{repo}/{kind}/main/"
                        + quote(source.relative_to(root).as_posix()))
        raise ValueError(f"No repository mapping for {source}")

    def rewrite(text, source, page):
        fenced = False
        result = []

        def link(match):
            image, label, target = match.groups()
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                return match[0]
            suffix = ("?" + parsed.query if parsed.query else "")
            suffix += "#" + parsed.fragment if parsed.fragment else ""
            local = (source.parent / unquote(parsed.path)).resolve()
            alias = aliases.get(local)
            if isinstance(alias, str):
                return f"{image}[{label}]({alias}{suffix})"
            local = alias or local
            # Site-owned links name generated pages rather than source files.
            if source.parent == CONTENT and parsed.path.endswith(".html"):
                return match[0]
            if not allowed(local) or not local.exists():
                raise ValueError(f"{source}: missing or out-of-scope link target: {target}")
            if local.is_dir():
                readme = local / "README.md"
                if not readme.is_file():
                    href = repository_link(local)
                    return f"{image}[{label}]({href}{suffix})"
                local = readme
            if local.suffix.lower() == ".md":
                if local not in sources:
                    href = repository_link(local)
                    return f"{image}[{label}]({href}{suffix})"
                dest = sources[local]
            else:
                asset_path = local.relative_to(workspace if workspace else compiler_doc.parent)
                dest = Path("assets") / asset_path
                assets[local] = dest
            href = quote(relative(dest, page), safe="/.-")
            return f"{image}[{label}]({href}{suffix})"

        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                fenced = not fenced
                result.append(line)
            elif fenced:
                result.append(line)
            else:
                # Do not rewrite example Markdown inside inline code.
                parts = re.split(r"(`[^`]+`)", line)
                result.append("".join(p if p.startswith("`") else LINK.sub(link, p) for p in parts))
        return "\n".join(result)

    rendered = {}
    for source, page in sources.items():
        raw = source.read_text(encoding="utf-8")
        if workspace and source == (workspace / "cmacros/examples/README.md").resolve():
            examples = source.parent
            runner = examples / "run_examples.py"
            license_file = examples / "original-passing/LICENSE"
            for required in (runner, license_file):
                if not required.is_file():
                    raise ValueError(f"Required cmacros example file missing: {required}")
            files = [runner, license_file]
            files += sorted((examples / "original-passing").glob("*.txt"))
            files += sorted((examples / "expected").glob("*.out"))
            raw += "\n\n## Example source files\n\n"
            raw += "\n".join(
                f"- [{p.relative_to(examples).as_posix()}]({quote(p.relative_to(examples).as_posix())})"
                for p in files)
        body = md_to_html(rewrite(raw, source, page))
        if workspace and source in sections["cmacros"]:
            body += f'\n<p><a href="{repository_link(source)}">Canonical source on GitHub</a></p>'
        rendered[source] = (raw, body)
    reserved = set(sources) | set(assets)
    if any(output == root or output in root.parents for root in source_roots):
        raise ValueError("Output must not replace a documentation source directory")
    if any(output == path or output in path.parents for path in reserved):
        raise ValueError("Output must not contain documentation inputs")
    protected = [CONTENT, compiler_doc]
    if workspace:
        protected += [workspace / name for name in ("editor", "debugger", "cmacros", "doc")]
    if output != ROOT / "site" and any(root in output.parents for root in protected):
        raise ValueError("Output must be outside documentation source trees")

    pages = {}
    for source, (raw, body) in rendered.items():
        page = sources[source]
        title = headings(raw)[0][1] if headings(raw) else source.stem
        pages[page] = (title, body)
    lines = ["<h1>Documentation</h1>"]
    for key, title in SECTIONS:
        lines.append(f'<h2 id="{key}">{title}</h2>')
        if not sections[key]:
            lines.append("<p>This section requires a complete workspace documentation input.</p>")
            continue
        lines.append('<ol class="toc">')
        for source in sections[key]:
            raw = rendered[source][0]
            title = headings(raw)[0][1] if headings(raw) else source.stem
            href = quote(sources[source].as_posix())
            lines.append(f'<li><a href="{href}">{html.escape(title)}</a>')
            subs = [h for h in headings(raw) if h[0] == 2]
            if subs:
                lines.append("<ol>")
                lines.extend(f'<li><a href="{href}#{anchor}">{html.escape(t)}</a></li>'
                             for _, t, anchor in subs)
                lines.append("</ol>")
            lines.append("</li>")
        lines.append("</ol>")
    pages[Path("docs.html")] = ("Documentation", "\n".join(lines))
    redirects = {
        Path(source.stem + ".html"): page
        for source, page in sources.items()
        if source.parent == compiler_doc and Path(source.stem + ".html") not in pages
    }
    for old, new in aliases.items():
        if isinstance(new, Path):
            redirects[Path(old.stem + ".html")] = sources[new]
    output.mkdir(parents=True, exist_ok=True)
    for page, (title, body) in pages.items():
        target = output / page
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(TEMPLATE.format(
            title=html.escape(title if title == "Cwhip" else title + " — Cwhip"),
            root="../" * (len(page.parts) - 1), body=body), encoding="utf-8")
    for old, new in redirects.items():
        href = quote(new.as_posix())
        (output / old).write_text(
            '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<title>Documentation moved — Cwhip</title><link rel="canonical" href="{href}">'
            f'<meta http-equiv="refresh" content="0;url={href}">'
            '</head><body>'
            f'<p>This document has moved to <a href="{href}">{href}</a>.</p>'
            f'<script>location.replace({json.dumps(href)} + location.hash);</script>'
            '</body></html>', encoding="utf-8")
    for source, dest in assets.items():
        (output / dest).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output / dest)
    for asset in ("styles.css", "app.js"):
        shutil.copy2(CONTENT / asset, output / asset)
    generated = {p.as_posix() for p in pages}
    generated.update(p.as_posix() for p in redirects)
    generated.update(p.as_posix() for p in assets.values())
    generated.update(("styles.css", "app.js"))
    state = output / ".generated-files.json"
    if state.exists():
        previous = json.loads(state.read_text(encoding="utf-8"))
        if not isinstance(previous, list) or not all(isinstance(p, str) for p in previous):
            raise ValueError(f"Invalid generated-file inventory: {state}")
        for name in set(previous) - generated:
            target = (output / name).resolve()
            if output not in target.parents:
                raise ValueError(f"Out-of-scope generated-file inventory entry: {name}")
            if target.is_file():
                target.unlink()
    state.write_text(json.dumps(sorted(generated), indent=2) + "\n", encoding="utf-8")
    check_site(output, list(pages) + list(redirects))
    print(f"Built {len(pages)} pages and {len(redirects)} compatibility redirects "
          f"in {output}; publication is manual.")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Root containing compiler/, editor/, debugger/, cmacros/, doc/")
    parser.add_argument("--docs-dir", type=Path, help="Compiler-only Markdown directory (partial site)")
    parser.add_argument("--output-dir", type=Path, help="Generated output (default: website/site)")
    args = parser.parse_args()
    try:
        build(args.workspace, args.docs_dir, args.output_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"website: {error}\n")


if __name__ == "__main__":
    main()
