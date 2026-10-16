#!/usr/bin/env python3
"""Check generated local links, fragments, stylesheets, scripts, and images."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])


def check_site(site, pages=None):
    site = Path(site).resolve()
    selected = list(pages) if pages is not None else [
        p.relative_to(site) for p in site.rglob("*.html")]
    parsed = {Path(p): Page((site / p).read_text(encoding="utf-8")) for p in selected}
    errors = []
    for path, page in parsed.items():
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = (site / path.parent / unquote(url.path)).resolve() if url.path else site / path
            if target.is_dir():
                target /= "index.html"
            if site not in target.parents or not target.is_file():
                errors.append(f"{path}: missing local target {href}")
                continue
            if url.fragment and target.suffix == ".html":
                key = target.relative_to(site)
                if key not in parsed:
                    parsed_page = Page(target.read_text(encoding="utf-8"))
                else:
                    parsed_page = parsed[key]
                if unquote(url.fragment) not in parsed_page.ids:
                    errors.append(f"{path}: missing fragment {href}")
    if errors:
        raise ValueError("Invalid generated site:\n" + "\n".join(errors))
    return len(selected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    try:
        count = check_site(args.site)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Checked {count} HTML pages: local links, fragments and assets exist.")


if __name__ == "__main__":
    main()
