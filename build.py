#!/usr/bin/env python3
"""
Minimal static site builder for Cwhip.
Requires: Python 3. No external libraries.

Expected layout when run from doc/website/:
  ../                  ← the real documentation Markdown files
  content/docs.md      ← manifest (which documents appear, and in what order)
  content/*.md         ← site-specific pages (index, about, …)
  site/                ← generated HTML (created by this script)

Run: python3 build.py
"""
import re, html
from pathlib import Path

CONTENT = Path("content")
PARENT = Path("..")
SITE = Path("site")
SITE.mkdir(exist_ok=True)

# Copy static assets from content/ into site/
for asset in ("styles.css", "app.js"):
    src = CONTENT / asset
    if src.exists():
        (SITE / asset).write_bytes(src.read_bytes())
        print(f"Copied {asset}")
    else:
        print(f"warning: {asset} not found in content/")

# ------------------------------------------------------------------
# Markdown → HTML (paragraphs separated by blank lines)
# ------------------------------------------------------------------
def inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md_to_html(text):
    lines = text.splitlines()
    out = []
    in_list = False
    in_code = False
    in_table = False
    para = []
    table_rows = []

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + "<br>\n".join(inline(p) for p in para) + "</p>")
            para = []

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            return
        out.append("<table>")
        for i, row in enumerate(table_rows):
            tag = "th" if i == 0 else "td"
            cells = [c.strip() for c in row.strip("|").split("|")]
            out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
        out.append("</table>")
        table_rows = []
        in_table = False

    for line in lines:
        if line.startswith("```"):
            flush_para()
            flush_table()
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line))
            continue

        stripped = line.strip()
        if not stripped:
            flush_para()
            flush_table()
            if in_list:
                out.append("</ul>")
                in_list = False
            continue

        # table row
        if "|" in line and line.strip().startswith("|"):
            flush_para()
            if not in_table:
                in_table = True
            # skip separator line |---|---|
            if re.match(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", line):
                continue
            table_rows.append(line)
            continue
        else:
            flush_table()

        if line.startswith("# "):
            flush_para()
            t = line[2:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            out.append(f'<h1 id="{anchor}">{inline(t)}</h1>')
        elif line.startswith("## "):
            flush_para()
            t = line[3:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            out.append(f'<h2 id="{anchor}">{inline(t)}</h2>')
        elif line.startswith("### "):
            flush_para()
            t = line[4:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            out.append(f'<h3 id="{anchor}">{inline(t)}</h3>')
        elif line.startswith(("- ", "* ")):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif re.match(r"^\d+\.\s", line):
            flush_para()
            if not in_list:
                out.append("<ol>")
                in_list = True
            content = re.sub(r"^\d+\.\s*", "", line)
            out.append(f"<li>{inline(content)}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            para.append(line)

    flush_para()
    flush_table()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)

# ------------------------------------------------------------------
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="top">
  <a class="logo" href="index.html">cwhip</a>
  <nav class="main-nav">
    <a href="index.html">Home</a>
    <a href="docs.html">Documentation</a>
    <a href="about-site.html">About this site</a>
    <a href="https://github.com/chucktilbury/cwhip">GitHub</a>
  </nav>
</header>
<main>
{body}
</main>
<footer>
  <p>Cwhip. Documentation source of truth is the repository.</p>
</footer>
<script src="app.js"></script>
</body>
</html>
"""

# ------------------------------------------------------------------
# Discover sources
# ------------------------------------------------------------------
source_files = {}
# Prefer parent directory (the real doc/ when running from doc/website)
for p in PARENT.glob("*.md"):
    source_files[p.name] = p
# Site-specific pages and any fallback copies in content/
for p in CONTENT.glob("*.md"):
    if p.name == "docs.md":
        continue
    if p.name not in source_files:
        source_files[p.name] = p

def rewrite_links(text):
    def replacer(m):
        label, target = m.group(1), m.group(2)
        # Handle optional #anchor
        path_part, _, anchor = target.partition("#")
        if path_part.endswith(".md"):
            html_name = Path(path_part).with_suffix(".html").name
            md_name = Path(path_part).name
            if md_name not in source_files:
                print(f"  warning: link target {target} will not have a generated HTML page")
            new_target = html_name + ("#" + anchor if anchor else "")
            return f"[{label}]({new_target})"
        return m.group(0)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replacer, text)

def extract_headings(path):
    if not path or not path.exists():
        return []
    heads = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            t = line[3:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
            heads.append((t, anchor))
    return heads

# ------------------------------------------------------------------
# Build pages
# ------------------------------------------------------------------
for name, path in source_files.items():
    raw = path.read_text(encoding="utf-8", errors="replace")
    title = "Cwhip"
    if raw.startswith("# "):
        title = raw.splitlines()[0][2:].strip()
    page_title = title if title == "Cwhip" else f"{title} — Cwhip"
    body = md_to_html(rewrite_links(raw))
    (SITE / f"{Path(name).stem}.html").write_text(
        TEMPLATE.format(title=page_title, body=body), encoding="utf-8")
    print(f"Built {Path(name).stem}.html")

# ------------------------------------------------------------------
# Generated documentation index from content/docs.md
# ------------------------------------------------------------------
def build_docs_index():
    man = CONTENT / "docs.md"
    if not man.exists():
        print("warning: content/docs.md missing")
        return
    lines = [
        "<h1>Documentation</h1>",
        "<p>Ordered list controlled by content/docs.md. Nested links come from headings.</p>",
        '<ol class="toc">',
    ]
    for line in man.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"-\s*\[([^\]]+)\]\(([^)]+)\)", line.strip())
        if not m:
            continue
        title, href = m.group(1), m.group(2)
        # Preserve directory paths; only rewrite bare .md names
        if href.endswith(".md"):
            html_name = Path(href).with_suffix(".html").name
        else:
            html_name = href          # e.g. html/index.html stays intact
        md_name = Path(href).name
        md_path = source_files.get(md_name)
        if href.endswith(".md") and md_path is None:
            print(f"  warning: manifest lists {href} but no source file was found")
            md_path = PARENT / md_name
        lines.append(f'<li><a href="{html_name}">{html.escape(title)}</a>')
        subs = extract_headings(md_path) if md_path else []
        if subs:
            lines.append("<ol>")
            for text, anchor in subs:
                lines.append(f'<li><a href="{html_name}#{anchor}">{html.escape(text)}</a></li>')
            lines.append("</ol>")
        lines.append("</li>")
    lines.append("</ol>")
    (SITE / "docs.html").write_text(
        TEMPLATE.format(title="Documentation — Cwhip", body="\n".join(lines)),
        encoding="utf-8")
    print("Built docs.html")

build_docs_index()
print("Done. Contents of site/ are ready to copy to the web root.")
