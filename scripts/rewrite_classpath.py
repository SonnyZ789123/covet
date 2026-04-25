# Copyright (c) 2025-2026 Yoran Mertens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#!/usr/bin/env python3

import sys


def rewrite_classpath(original_dir: str, new_prefix: str, classpath: str) -> str:
    if not classpath:
        return ""

    parts = [p.strip() for p in classpath.split(":") if p.strip()]

    rewritten = []
    for p in parts:
        if p == original_dir or p.startswith(original_dir + "/"):
            rewritten.append(p.replace(original_dir, new_prefix, 1))
        else:
            raise RuntimeError(f"Error: Classpath entry '{p}' does not start with original deps dir '{original_dir}'")

    return ":".join(rewritten)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: rewrite_classpath.py <ORIGINAL_DEPS_DIR> <NEW_DEPS_PREFIX> <CLASSPATH>",
            file=sys.stderr,
        )
        sys.exit(1)

    original_dir = sys.argv[1].rstrip("/")
    new_prefix = sys.argv[2].rstrip("/")
    classpath = sys.argv[3].strip()

    cp = rewrite_classpath(original_dir, new_prefix, classpath)
    print(cp)