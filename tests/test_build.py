import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import build
from check_site import check_site


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cwhip site ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.output = self.root / "site output"
        self.write("compiler/doc/INSTALLATION.md", "# Installation\n\n## Build\n")
        self.write("compiler/doc/README.md", "# Compiler docs\n")
        self.write("compiler/doc/CEDIT.md", "# OBSOLETE EDITOR\n")
        self.write("compiler/doc/CDBG.md", "# OBSOLETE DEBUGGER\n")
        self.write("editor/CEDIT.md", "# Editor guide\n\n[Build](doc/BUILD.md)\n")
        self.write("editor/doc/BUILD.md", "# Editor build\n\n[Guide](../CEDIT.md)\n")
        self.write("debugger/CDBG.md", "# Debugger guide\n")
        self.write("debugger/doc/BUILD.md", "# Debugger build\n")
        self.write("doc/FIRST-PROGRAM.md", "# First program\n\n[Build](BUILD.md)\n")
        self.write("doc/BUILD.md", "# Workflow build\n\n[Compiler](../compiler/doc/INSTALLATION.md#build)\n")

    def write(self, name, text):
        target = self.workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def run_build(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return build.build(workspace=self.workspace, output_dir=self.output, **kwargs)

    def test_complete_site_and_section_collisions(self):
        self.run_build()
        check_site(self.output)
        toc = (self.output / "docs.html").read_text()
        for key, title in build.SECTIONS:
            self.assertIn(f'id="{key}"', toc)
            self.assertIn(title, toc)
        self.assertIn("Editor build", (self.output / "editor/doc/BUILD.html").read_text())
        self.assertIn("Debugger build", (self.output / "debugger/doc/BUILD.html").read_text())
        self.assertIn("Workflow build", (self.output / "workflow/BUILD.html").read_text())
        self.assertIn('../../styles.css', (self.output / "editor/doc/BUILD.html").read_text())
        self.assertFalse((self.output / "compiler/CEDIT.html").exists())
        self.assertNotIn("html/index.html", toc)
        self.assertIn('href="compiler/INSTALLATION.html"',
                      (self.output / "INSTALLATION.html").read_text())
        self.assertIn('href="editor/CEDIT.html"', (self.output / "CEDIT.html").read_text())
        self.assertIn("location.hash", (self.output / "CEDIT.html").read_text())

    def test_authoritative_aliases(self):
        self.write("compiler/doc/INSTALLATION.md",
                   "# Install\n\n## Build\n\n[Editor](CEDIT.md) and [Debugger](CDBG.md)\n")
        self.run_build()
        page = (self.output / "compiler/INSTALLATION.html").read_text()
        self.assertIn('../editor/CEDIT.html', page)
        self.assertIn('../debugger/CDBG.html', page)
        self.assertNotIn("OBSOLETE", page)

    def test_linked_asset_and_repository_reference(self):
        self.write("compiler/doc/figure.svg", "<svg></svg>")
        self.write("compiler/stdlib/README.md", "# External source README\n")
        self.write("compiler/doc/README.md",
                   "# Docs\n\n![Figure](figure.svg)\n\n[Library](../stdlib/README.md)\n")
        self.run_build()
        page = (self.output / "compiler/README.html").read_text()
        self.assertIn('<img src="../assets/compiler/doc/figure.svg"', page)
        self.assertIn("https://github.com/chucktilbury/cwhip/blob/main/stdlib/README.md", page)
        self.assertTrue((self.output / "assets/compiler/doc/figure.svg").is_file())

    def test_missing_source_fails_before_output(self):
        (self.workspace / "doc/FIRST-PROGRAM.md").unlink()
        with self.assertRaisesRegex(ValueError, "first-program guide"):
            self.run_build()
        self.assertFalse(self.output.exists())

    def test_broken_links_and_fragments_fail(self):
        source = self.write("editor/CEDIT.md", "# Editor\n\n[Missing](missing.md)\n")
        with self.assertRaisesRegex(ValueError, "missing or out-of-scope"):
            self.run_build()
        source.write_text("# Editor\n\n[Missing](#missing)\n")
        with self.assertRaisesRegex(ValueError, "missing fragment"):
            self.run_build()

    def test_stale_generated_files_removed_manual_api_preserved(self):
        extra = self.write("compiler/doc/OLD.md", "# Old\n")
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
             "--workspace", str(self.workspace), "--output-dir", str(self.output)],
            cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        check_site(self.output)

    def test_no_input_is_explicit_error(self):
        # This standalone checkout is not the old doc/website staging layout.
        if (build.ROOT.parent / "INSTALLATION.md").is_file():
            self.skipTest("legacy adapter staging")
        with self.assertRaisesRegex(ValueError, "Documentation input required"):
            build.build(output_dir=self.output)

    def test_compiler_only_partial_build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            build.build(docs_dir=self.workspace / "compiler/doc", output_dir=self.output)
        check_site(self.output)
        self.assertIn("complete workspace", (self.output / "docs.html").read_text())

    def test_legacy_staging_fallback(self):
        stage = self.root / "legacy/doc"
        shutil.copytree(self.workspace / "compiler/doc", stage)
        website = stage / "website"
        shutil.copytree(build.CONTENT, website / "content")
        for name in ("build.py", "check_site.py"):
            shutil.copy2(build.ROOT / name, website / name)
        result = subprocess.run(
            [sys.executable, str(website / "build.py")],
            cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        check_site(website / "site")

    def test_output_cannot_overwrite_source(self):
        for output in (self.workspace, self.workspace / "compiler/doc",
                       self.workspace / "editor/generated"):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "Output must"):
                    with contextlib.redirect_stdout(io.StringIO()):
                        build.build(workspace=self.workspace, output_dir=output)

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
