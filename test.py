#!/usr/bin/env python
# pylint: disable=all

import re
import os
import shutil

TEST_TEMPLATE = re.compile("<!--- snippet-template: ([^ ]+) -->")
SNIPPET_NAME = re.compile("<!--- snippet-name: ([^ ]+) -->")


def main():
    in_snippet = False
    snippet = []
    snippets = []
    template = "program"
    snippet_template = None

    for (line_nr, line) in enumerate(open("slides.md")):
        trimmed_line = line.strip()
        if trimmed_line == "```rust":
            in_snippet = True
            snippet_template = template
            snippet = []
            continue

        m = TEST_TEMPLATE.match(trimmed_line)
        if m:
            template = m.groups(0)[0]
        m = SNIPPET_NAME.match(trimmed_line)
        if m:
            snippet_name = m.groups(0)[0]

        if in_snippet:
            if trimmed_line == "```":
                snippet = "\n".join(snippet)
                if snippet_name:
                    snippets.append((snippet, snippet_name, line_nr,
                                    snippet_template))
                in_snippet = False
                snippet_template = "program"
                snippet_name = None
                continue
            snippet.append(line)

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdirname:
        names = []
        for (snippet, snippet_name, line_nr, template) in snippets:
            names.append(snippet_name)
            tmppath = os.path.join(tmpdirname, snippet_name)
            template_path = os.path.join("templates", template)
            try:
                shutil.rmtree(os.path.join(template_path, "target"))
            except OSError:
                pass
            shutil.copytree(template_path, tmppath)

            for root, dirnames, filenames in os.walk(tmppath):
                for filename in filenames:
                    fullpath = os.path.join(root, filename)
                    hook = "/// ADD CODE"
                    content = open(fullpath).read()
                    if hook in content:
                        lines = "\n".join(([""] * (line_nr - 1)))
                        content = content.replace(hook, lines + snippet)
                        open(fullpath, "w").write(content)

            toml = os.path.join(tmppath, "Cargo.toml")
            content = open(toml).read().replace("REPLACENAME", snippet_name)
            open(toml, "w").write(content)

        main_cargo_file = (os.path.join(tmpdirname, "Cargo.toml"))
        names = repr(names)
        open(main_cargo_file, "w").write(f"""

[workspace]
members = {names}
""")

        for (snippet, snippet_name, line_nr, template) in snippets:
            print(f"Testing snippet {snippet_name} at line {line_nr}")
            tmppath = os.path.join(tmpdirname, snippet_name)
            os.system(f"cd {tmppath} && cargo build -q")


if __name__ == "__main__":
    main()
