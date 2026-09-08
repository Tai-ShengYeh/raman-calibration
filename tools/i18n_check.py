#!/usr/bin/env python3
"""Small, dependency-free checker for the bilingual HTML contract."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


CJK_RE = re.compile(r"[\u4e00-\u9fff、，「」（）：；！？．。]" )
IGNORED_TAGS = {"script", "style", "pre", "code", "kbd", "svg", "textarea", "input", "button", "a", "h1", "h2", "nav"}
ATTRS = {
    "title": "data-en-title",
    "placeholder": "data-en-placeholder",
    "alt": "data-en-alt",
    "aria-label": "data-en-aria-label",
}


class Node:
    def __init__(self, tag, attrs, line, parent=None):
        self.tag = tag
        self.attrs = dict(attrs)
        self.line = line
        self.parent = parent
        self.children = []

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())


class Text:
    def __init__(self, data, line):
        self.data = data
        self.line = line


class Checker(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.root = Node("#document", {}, 1)
        self.stack = [self.root]
        self.hard = []
        self.warn = []
        self.script_chunks = []
        self.pair_count = 0
        self.en_pair_count = 0
        self.data_en_count = 0
        self.refs = {"i18n.css": False, "i18n.js": False, "glossary.js": False}

    def current(self):
        return self.stack[-1]

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), attrs, self.getpos()[0], self.current())
        self.current().children.append(node)
        self.stack.append(node)
        for name in node.attrs:
            if name.startswith("data-en"):
                self.data_en_count += 1
        if tag.lower() == "link" and node.attrs.get("href") and "i18n.css" in node.attrs["href"]:
            self.refs["i18n.css"] = True
        if tag.lower() == "script" and node.attrs.get("src"):
            src = node.attrs["src"]
            for key in ("i18n.js", "glossary.js"):
                if key in src:
                    self.refs[key] = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.current().children.append(Text(data, self.getpos()[0]))
        if not CJK_RE.search(data):
            return
        tags = {node.tag for node in self.stack}
        classes = set().union(*(node.classes for node in self.stack))
        if tags & IGNORED_TAGS or "i18n-toggle" in classes:
            if "script" in tags:
                self.script_chunks.append((self.getpos()[0], data))
            return
        self.script_chunks.append((self.getpos()[0], data)) if "script" in tags else None
        language = None
        for node in reversed(self.stack):
            if node.tag == "html":
                break  # the root lang is the page default, not a translation wrapper
            if "lang" in node.attrs:
                language = node.attrs["lang"]
                break
        in_term_alt = any("term-alt" in node.classes for node in self.stack)
        if language != "zh-Hant" and not in_term_alt:
            self.hard.append((self.getpos()[0], "CJK text outside lang=zh-Hant", data))
        if language == "en" and not in_term_alt:
            self.hard.append((self.getpos()[0], "CJK text inside lang=en", data))

    def handle_comment(self, data):
        return

    def finish(self):
        self.check_attributes()
        self.check_pairs(self.root)
        for line_no, data in self.script_chunks:
            if "zh:" not in data:
                self.warn.append((line_no, "script text contains CJK without zh:", data))

    def check_attributes(self):
        def walk(node):
            if isinstance(node, Text):
                return
            for attr, data_attr in ATTRS.items():
                value = node.attrs.get(attr)
                if value and CJK_RE.search(value) and data_attr not in node.attrs:
                    self.warn.append((node.line, f"{attr} contains CJK without {data_attr}", value))
            for child in node.children:
                walk(child)
        walk(self.root)

    @staticmethod
    def meaningful_siblings(parent, node):
        try:
            index = parent.children.index(node)
        except ValueError:
            return None, None
        before = None
        for item in reversed(parent.children[:index]):
            if isinstance(item, Text) and not item.data.strip():
                continue
            before = item
            break
        after = None
        for item in parent.children[index + 1:]:
            if isinstance(item, Text) and not item.data.strip():
                continue
            after = item
            break
        return before, after

    def check_pairs(self, node):
        if isinstance(node, Text):
            return
        if "i18n-toggle" not in node.classes and node.tag == "span":
            language = node.attrs.get("lang")
            before, after = self.meaningful_siblings(node.parent, node) if node.parent else (None, None)
            before_lang = before.attrs.get("lang") if isinstance(before, Node) else None
            after_lang = after.attrs.get("lang") if isinstance(after, Node) else None
            if language == "zh-Hant":
                if after_lang != "en":
                    self.hard.append((node.line, "lang=zh-Hant span is unpaired", node.attrs.get("class", "span")))
                else:
                    self.pair_count += 1
            elif language == "en":
                if before_lang != "zh-Hant":
                    self.hard.append((node.line, "lang=en span is unpaired", node.attrs.get("class", "span")))
                else:
                    self.en_pair_count += 1
        for child in node.children:
            self.check_pairs(child)


def snippet(value):
    return " ".join(value.strip().split())[:60]


def check_file(path):
    source = path.read_text(encoding="utf-8")
    parser = Checker(source)
    parser.feed(source)
    parser.close()
    parser.finish()
    print(f"FILE: {path}")
    for line, reason, value in parser.hard:
        print(f"HARD line {line}: {reason}: {snippet(value)}")
    for line, reason, value in parser.warn:
        print(f"WARN line {line}: {reason}: {snippet(value)}")
    print(f"INFO: zh/en pairs found: {parser.pair_count} (zh), {parser.en_pair_count} (en)")
    print(f"INFO: total data-en-* attributes: {parser.data_en_count}")
    print("INFO: references: " + ", ".join(f"{key}={'yes' if value else 'no'}" for key, value in parser.refs.items()))
    return bool(parser.hard)


def main(argv):
    if not argv:
        print("usage: python tools/i18n_check.py FILE [FILE ...]", file=sys.stderr)
        return 2
    return 1 if any(check_file(Path(name)) for name in argv) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
