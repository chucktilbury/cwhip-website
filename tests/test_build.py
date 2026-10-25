import contextlib
import html
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import build
from check_site import check_site


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cwhip site ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repos = self.root / "independent repos"
        self.output = self.root / "site output"
        self.write("cwhip/doc/INSTALLATION.md", "# Installation\n\n## Build\n")
        self.write("cwhip/doc/GETTING_STARTED.md",
                   "# Getting started\n\n[Installation](INSTALLATION.md#build)\n")
        self.write("cwhip/doc/README.md", "# Compiler docs\n")
        self.write("cwhip/doc/CEDIT.md", "# OBSOLETE EDITOR\n")
        self.write("cwhip/doc/CDBG.md", "# OBSOLETE DEBUGGER\n")
        self.write("cedit/CEDIT.md", "# Editor guide\n\n[Build](doc/BUILD.md)\n")
        self.write("cedit/doc/BUILD.md", "# Editor build\n\n[Guide](../CEDIT.md)\n")
        self.write("cdbg/CDBG.md", "# Debugger guide\n")
        self.write("cdbg/doc/BUILD.md", "# Debugger build\n")
        self.write("cmacros/README.md",
                   "# cmacros\n\n[Language](doc/LANGUAGE.md#names)\n\n"
                   "[Original inputs](examples/original-passing)\n\n"
                   "[Examples](examples/README.md#run)\n")
        self.write("cmacros/doc/BUILD.md", "# Macro build\n")
        self.write("cmacros/doc/LANGUAGE.md", "# Macro language\n\n## Names\n")
        self.write("cmacros/doc/DIAGNOSTICS.md", "# Macro diagnostics\n")
        self.write("cmacros/examples/README.md",
                   "# Original macros examples\n\n## Run\n\n"
                   "[Upstream](https://github.com/chucktilbury/macros/tree/commit/tests/passing)\n")
        self.write("cmacros/examples/run_examples.py", 'print("runner")\n')
        self.write("cmacros/examples/original-passing/LICENSE", "MIT attribution\n")
        self.write("cmacros/examples/original-passing/define.txt",
                   "# Not Markdown\n[x](missing.md)\n.define X {<tag>}\n@X\n")
        self.write("cmacros/examples/expected/define.out", "<tag>\n")
        self.write("cwhip/doc/FIRST-PROGRAM.md",
                   "# First program\n\n[Build](INSTALLATION.md#build)\n")

    def write(self, name, text):
        target = self.source(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def source(self, name):
        return self.repos / name

    def run_build(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return build.build(repos_root=self.repos, output_dir=self.output, **kwargs)

    def test_complete_site_and_section_collisions(self):
        self.run_build()
        check_site(self.output)
        toc = (self.output / "docs.html").read_text()
        for key, title in build.SECTIONS:
            self.assertIn(f'id="{key}"', toc)
            self.assertIn(title, toc)
        self.assertIn("Editor build", (self.output / "editor/doc/BUILD.html").read_text())
        self.assertIn("Debugger build", (self.output / "debugger/doc/BUILD.html").read_text())
        self.assertIn("Macro build", (self.output / "cmacros/doc/BUILD.html").read_text())
        self.assertFalse((self.output / "workflow").exists())
        self.assertNotIn('id="workflow"', toc)
        self.assertIn('href="getting-started/FIRST-PROGRAM.html"', toc)
        self.assertFalse((self.output / "compiler/FIRST-PROGRAM.html").exists())
        getting_started = (self.output / "getting-started/index.html").read_text()
        self.assertIn("<h1 id=\"getting-started\">Getting started</h1>", getting_started)
        self.assertIn('href="../compiler/INSTALLATION.html#build"', getting_started)
        self.assertIn('href="docs.html#getting-started"', (self.output / "index.html").read_text())
        self.assertIn('href="getting-started/index.html"', toc)
        self.assertIn('href="../docs.html#getting-started"', getting_started)
        self.assertIn("Getting started", toc)
        self.assertIn('../../styles.css', (self.output / "editor/doc/BUILD.html").read_text())
        self.assertFalse((self.output / "compiler/GETTING_STARTED.html").exists())
        self.assertFalse((self.output / "compiler/CEDIT.html").exists())
        self.assertNotIn("html/index.html", toc)
        self.assertIn('href="compiler/INSTALLATION.html"',
                      (self.output / "INSTALLATION.html").read_text())
        self.assertIn('href="editor/CEDIT.html"', (self.output / "CEDIT.html").read_text())
        self.assertIn("location.hash", (self.output / "CEDIT.html").read_text())

    def test_cmacros_navigation_raw_examples_and_provenance(self):
        self.run_build()
        toc = (self.output / "docs.html").read_text()
        home = (self.output / "index.html").read_text()
        self.assertIn('href="docs.html#cmacros"', home)
        self.assertIn('href="cmacros/README.html"', toc)
        self.assertIn('href="cmacros/examples/README.html#example-source-files"', toc)
        readme = (self.output / "cmacros/README.html").read_text()
        self.assertIn('href="doc/LANGUAGE.html#names"', readme)
        self.assertIn('href="examples/README.html#run"', readme)
        self.assertIn("https://github.com/chucktilbury/cmacros/tree/main/examples/original-passing",
                      readme)
        guide = (self.output / "cmacros/examples/README.html").read_text()
        self.assertIn("https://github.com/chucktilbury/macros/tree/commit/tests/passing", guide)
        self.assertIn("https://github.com/chucktilbury/cmacros/blob/main/examples/README.md", guide)
        for name in ("run_examples.py", "original-passing/LICENSE",
                     "original-passing/define.txt", "expected/define.out"):
            self.assertIn(f'href="../../assets/cmacros/examples/{name}"', guide)
            self.assertEqual((self.output / "assets/cmacros/examples" / name).read_bytes(),
                             (self.repos / "cmacros/examples" / name).read_bytes())
        self.assertFalse((self.output / "cmacros/examples/original-passing/define.html").exists())
        check_site(self.output)

    def test_cmacros_required_inputs_fail_before_output(self):
        for name in ("README.md", "doc/BUILD.md", "doc/LANGUAGE.md",
                     "doc/DIAGNOSTICS.md", "examples/README.md",
                     "examples/run_examples.py", "examples/original-passing/LICENSE"):
            with self.subTest(name=name):
                source = self.repos / "cmacros" / name
                text = source.read_text()
                source.unlink()
                with self.assertRaisesRegex(ValueError, "Required cmacros"):
                    self.run_build()
                self.assertFalse(self.output.exists())
                source.write_text(text)

    def test_cmacros_repository_mapping_and_link_suffixes(self):
        self.write("cmacros/other/README.md", "# Other source\n")
        self.write("cmacros/doc/BUILD.md",
                   "# Macro build\n\n[Language](LANGUAGE.md?view=full#names)\n\n"
                   "[Other](../other/README.md?plain=1#other-source)\n\n"
                   "[Inputs](../examples/original-passing?plain=1#files)\n")
        self.run_build()
        page = (self.output / "cmacros/doc/BUILD.html").read_text()
        self.assertIn('href="LANGUAGE.html?view=full#names"', page)
        self.assertIn("https://github.com/chucktilbury/cmacros/blob/main/other/README.md"
                      "?plain=1#other-source", page)
        self.assertIn("https://github.com/chucktilbury/cmacros/tree/main/examples/"
                      "original-passing?plain=1#files", page)

    def test_cmacros_stale_assets_removed_in_partial_build(self):
        self.run_build()
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(docs_dir=self.source("cwhip/doc"), output_dir=self.output)
        self.assertFalse((self.output / "cmacros/README.html").exists())
        self.assertFalse((self.output / "assets/cmacros/examples/run_examples.py").exists())
        check_site(self.output)

    def test_authoritative_aliases(self):
        self.write("cwhip/doc/INSTALLATION.md",
                   "# Install\n\n## Build\n\n[Editor](CEDIT.md) and [Debugger](CDBG.md)\n")
        self.run_build()
        page = (self.output / "compiler/INSTALLATION.html").read_text()
        self.assertIn('../editor/CEDIT.html', page)
        self.assertIn('../debugger/CDBG.html', page)
        self.assertNotIn("OBSOLETE", page)

    def test_homepage_current_syntax(self):
        self.run_build()
        page = (self.output / "index.html").read_text()
        text = " ".join(page.split())
        self.assertIn(
            "<code>int</code>, <code>uint</code>, and <code>float</code> are native aliases "
            "for <code>int32</code>, <code>uint32</code>, and <code>fp32</code>, respectively.",
            text)
        self.assertIn("<code>unsigned</code> remains reserved and is not a type alias.", text)
        for sample in ("R<P1,P2>", "R<>", "int64<int64>", "int64<int64><String>",
                       "#", "//", "/* ... */", "[key: value]", "[:]", "[]",
                       "return(value)", "return()", "raise(exception)", "raise()",
                       "if (first) { ... } else (second) { ... } else { ... }",
                       "flags & mask == expected", "(flags & mask) == expected",
                       "int64 count = 42", "and", "&&", "or", "||", "not", "!"):
            with self.subTest(sample=sample):
                self.assertIn("<code>" + html.escape(sample) + "</code>", page)
        for guidance in ("<code>callback</code> is an ordinary identifier",
                         "Newlines delimit simple statements",
                         "neither a comment marker nor a statement separator",
                         "Both kinds of literal can span lines and have a trailing comma",
                         "a bare <code>else</code> must be last",
                         "bind more tightly than comparisons",
                         "Class fields may have compile-time constant initializers",
                         "Keywords are case-insensitive"):
            with self.subTest(guidance=guidance):
                self.assertIn(guidance, text)
        self.assertNotIn("reserved and rejected, not aliases", page)
        check_site(self.output)

    def test_current_cwhip_samples_preserved_on_import(self):
        sample = '''class Example {
    int64 count = 42
    int64<int64> callback
    int64<int64><String> factory
    int64 value() { return(count) }
}
start {
    # Dictionary and list literals can span lines.
    dict values = [
        "answer": 42,
    ]
    dict empty = [:]
    list items = [
        1,
        2,
    ]
    int flags = 3
    uint mask = 1u
    float fraction = .5
    IF (flags & 1 == 1 and not false) {
        print(values["answer"])
    } else (flags == 0 || false) {
        print(empty)
    } else {
        /* This is a block comment. */
        // A second line-comment spelling.
        print(items)
    }
    try {
        raise(Exception("example"))
    } except (Exception) {
        raise()
    }
}
'''
        source = self.write("cwhip/doc/SYNTAX.md", "# Syntax\n\n```cwhip\n" + sample + "```\n")
        original = source.read_bytes()
        for partial in (False, True):
            with self.subTest(partial=partial):
                with contextlib.redirect_stdout(io.StringIO()):
                    if partial:
                        build.build(docs_dir=self.source("cwhip/doc"), output_dir=self.output)
                    else:
                        self.run_build()
                page = (self.output / "compiler/SYNTAX.html").read_text()
                self.assertIn("<pre><code>\n" + html.escape(sample) + "</code></pre>", page)
                self.assertEqual(source.read_bytes(), original)
                check_site(self.output)

    def test_linked_asset_and_repository_reference(self):
        self.write("cwhip/doc/figure.svg", "<svg></svg>")
        self.write("cwhip/stdlib/README.md", "# External source README\n")
        self.write("cwhip/doc/README.md",
                   "# Docs\n\n![Figure](figure.svg)\n\n[Library](../stdlib/README.md)\n")
        self.run_build()
        page = (self.output / "compiler/README.html").read_text()
        self.assertIn('<img src="../assets/compiler/doc/figure.svg"', page)
        self.assertIn("https://github.com/chucktilbury/cwhip/blob/master/stdlib/README.md", page)
        self.assertTrue((self.output / "assets/compiler/doc/figure.svg").is_file())

    def test_code_formatted_link_labels_are_rewritten_and_rendered(self):
        self.write("cwhip/stdlib/README.md", "# Library\n")
        self.write("cwhip/doc/README.md",
                   "# Docs\n\n[Install (`cwhip`)](INSTALLATION.md#build)\n\n"
                   "[`stdlib`](../stdlib/README.md)\n\n"
                   "`[example](missing.md)`\n\n"
                   "```\n[`example`](missing.md)\n```\n")
        self.run_build()
        page = (self.output / "compiler/README.html").read_text()
        self.assertIn('<a href="INSTALLATION.html#build">Install (<code>cwhip</code>)</a>', page)
        self.assertIn('<a href="https://github.com/chucktilbury/cwhip/blob/master/'
                      'stdlib/README.md"><code>stdlib</code></a>', page)
        self.assertIn('<code>[example](missing.md)</code>', page)
        self.assertIn('[`example`](missing.md)', page)
        check_site(self.output)
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(docs_dir=self.source("cwhip/doc"), output_dir=self.output)
        partial = (self.output / "compiler/README.html").read_text()
        self.assertIn('<a href="INSTALLATION.html#build">Install (<code>cwhip</code>)</a>', partial)
        self.assertIn('/cwhip/blob/master/stdlib/README.md', partial)
        check_site(self.output)

    def test_inline_link_labels_and_targets_are_escaped(self):
        rendered = build.inline('[`a<b` & **bold**](https://example.test/?a=1&b=2)')
        self.assertEqual(
            rendered,
            '<a href="https://example.test/?a=1&amp;b=2">'
            '<code>a&lt;b</code> &amp; <strong>bold</strong></a>')
        self.assertEqual(build.inline('![a"b](image.png?x=1&y=2)'),
                         '<img src="image.png?x=1&amp;y=2" alt="a&quot;b">')
        self.assertEqual(build.inline('**[guide](guide.html)** and *`ab`*'),
                         '<strong><a href="guide.html">guide</a></strong> and '
                         '<em><code>ab</code></em>')

    def test_missing_source_fails_before_output(self):
        self.source("cwhip/doc/FIRST-PROGRAM.md").unlink()
        with self.assertRaisesRegex(ValueError, "first-program guide"):
            self.run_build()
        self.assertFalse(self.output.exists())

    def test_missing_getting_started_fails_before_output(self):
        self.source("cwhip/doc/GETTING_STARTED.md").unlink()
        with self.assertRaisesRegex(ValueError, "getting-started guide"):
            self.run_build()
        self.assertFalse(self.output.exists())

    def test_broken_links_and_fragments_fail(self):
        source = self.write("cedit/CEDIT.md", "# Editor\n\n[Missing](missing.md)\n")
        with self.assertRaisesRegex(ValueError, "missing or out-of-scope"):
            self.run_build()
        source.write_text("# Editor\n\n[Missing](#missing)\n")
        with self.assertRaisesRegex(ValueError, "missing fragment"):
            self.run_build()

    def test_stale_generated_files_removed_manual_api_preserved(self):
        extra = self.write("cwhip/doc/OLD.md", "# Old\n")
        self.run_build()
        manual = self.output / "html/index.html"
        manual.parent.mkdir()
        manual.write_text("<h1>Manual API</h1>")
        extra.unlink()
        self.run_build()
        self.assertFalse((self.output / "compiler/OLD.html").exists())
        self.assertFalse((self.output / "OLD.html").exists())
        self.assertTrue(manual.exists())

    def test_arbitrary_cwd_cli_and_paths_with_spaces(self):
        result = subprocess.run(
            [sys.executable, str(build.ROOT / "build.py"),
             "--repos-root", str(self.repos), "--output-dir", str(self.output)],
            cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        check_site(self.output)

    def test_default_sibling_discovery_without_workspace(self):
        website = self.repos / "cwhip-website"
        website.mkdir()
        with patch.object(build, "ROOT", website), contextlib.redirect_stdout(io.StringIO()):
            build.build(output_dir=self.output)
        check_site(self.output)
        self.assertEqual({p.name for p in self.repos.iterdir()},
                         {"cwhip", "cedit", "cdbg", "cmacros", "cwhip-website"})
        for page in self.output.rglob("*.html"):
            self.assertNotIn("cwhip-workspace", page.read_text())

    def test_missing_sibling_is_explicit_error(self):
        with self.assertRaisesRegex(ValueError, "No compiler documentation found"):
            build.build(repos_root=self.root / "absent", output_dir=self.output)
        self.assertFalse(self.output.exists())

    def test_explicit_repository_roots(self):
        self.write("cedit/doc/icon.svg", "<svg>editor</svg>")
        self.write("cdbg/doc/icon.svg", "<svg>debugger</svg>")
        for repo in ("cedit", "cdbg"):
            self.write(f"{repo}/doc/BUILD.md", "# Build\n\n![Icon](icon.svg)\n")
        roots = {}
        for repo in ("cwhip", "cedit", "cdbg", "cmacros"):
            target = self.root / f"separate {repo}" / "checkout"
            target.parent.mkdir()
            shutil.move(self.repos / repo, target)
            roots[f"{repo}_root"] = target
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(output_dir=self.output, **roots)
        check_site(self.output)
        self.assertTrue((self.output / "editor/CEDIT.html").is_file())
        for component in ("editor", "debugger"):
            asset = f"assets/{component}/doc/icon.svg"
            self.assertEqual((self.output / asset).read_text(), f"<svg>{component}</svg>")
            self.assertIn(f'../../{asset}',
                          (self.output / component / "doc/BUILD.html").read_text())

    def test_single_root_override_and_cross_repository_links(self):
        self.write("cwhip/doc/README.md",
                   "# Docs\n\n[Editor](../../cedit/CEDIT.md)\n")
        target = self.root / "separate macros"
        shutil.move(self.repos / "cmacros", target)
        self.run_build(cmacros_root=target)
        self.assertIn('href="../editor/CEDIT.html"',
                      (self.output / "compiler/README.html").read_text())
        check_site(self.output)

    def test_old_workflow_generated_pages_are_removed(self):
        self.run_build()
        stale = self.output / "workflow/BUILD.html"
        stale.parent.mkdir()
        stale.write_text("<h1>Old workflow</h1>")
        inventory = self.output / ".generated-files.json"
        inventory.write_text(json.dumps(json.loads(inventory.read_text()) + ["workflow/BUILD.html"]))
        self.run_build()
        self.assertFalse(stale.exists())

    def test_missing_component_guide_fails_before_output(self):
        for name in ("cedit/CEDIT.md", "cdbg/CDBG.md"):
            with self.subTest(name=name):
                source = self.source(name)
                text = source.read_text()
                source.unlink()
                with self.assertRaisesRegex(ValueError, "Required component guide missing"):
                    self.run_build()
                self.assertFalse(self.output.exists())
                source.write_text(text)

    def test_legacy_combined_layout_option_is_rejected(self):
        result = subprocess.run(
            [sys.executable, str(build.ROOT / "build.py"),
             "--workspace", str(self.repos), "--output-dir", str(self.output)],
            cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --workspace", result.stderr)
        self.assertFalse(self.output.exists())

    def test_partial_and_repository_inputs_are_mutually_exclusive(self):
        for roots in ({"repos_root": self.repos}, {"cedit_root": self.source("cedit")}):
            with self.subTest(roots=roots):
                with self.assertRaisesRegex(ValueError, "Use --docs-dir alone"):
                    build.build(docs_dir=self.source("cwhip/doc"),
                                output_dir=self.output, **roots)

    def test_compiler_only_partial_build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(docs_dir=self.source("cwhip/doc"), output_dir=self.output)
        check_site(self.output)
        self.assertTrue((self.output / "compiler/GETTING_STARTED.html").is_file())
        self.assertIn("standalone repositories", (self.output / "docs.html").read_text())
        toc = (self.output / "docs.html").read_text()
        self.assertIn('id="cmacros"', toc)
        self.assertNotIn('href="cmacros/', toc)
        self.assertIn('href="docs.html#cmacros"', (self.output / "index.html").read_text())

    def test_explicit_roots_cli(self):
        command = [sys.executable, str(build.ROOT / "build.py")]
        for repo in ("cwhip", "cedit", "cdbg", "cmacros"):
            command += [f"--{repo}-root", str(self.repos / repo)]
        result = subprocess.run(
            command + ["--output-dir", str(self.output)],
            cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        check_site(self.output)

    def test_output_cannot_overwrite_source(self):
        for output in (self.repos, self.source("cwhip/doc"),
                       self.source("cedit/generated"), self.repos / "cmacros/generated"):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "Output must"):
                    with contextlib.redirect_stdout(io.StringIO()):
                        build.build(repos_root=self.repos, output_dir=output)

    def test_markdown_lists_fences_headings_and_escaping(self):
        rendered = build.md_to_html(
            "1. First\n2. Second\n\n## Heading\n\n- Bullet\n  1. Nested\n\n"
            "```\n## Not a heading\n[x](missing.md)\n```\n\n"
            "## Heading\n\n`a*b*` and <tag>\n")
        self.assertEqual(rendered.count("<ol>"), rendered.count("</ol>"))
        self.assertEqual(rendered.count("<ul>"), rendered.count("</ul>"))
        self.assertIn('id="heading-1"', rendered)
        self.assertNotIn('id="not-a-heading"', rendered)
        self.assertIn("<code>a*b*</code>", rendered)
        self.assertIn("&lt;tag&gt;", rendered)

    def test_import_does_not_create_cwd_output(self):
        result = subprocess.run(
            [sys.executable, "-c", "import build"],
            cwd=self.root, env={**os.environ, "PYTHONPATH": str(build.ROOT)},
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "site").exists())


if __name__ == "__main__":
    unittest.main()
