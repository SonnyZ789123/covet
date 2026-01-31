#!/usr/bin/env python3
import sys


def rewrite_classpath(original_dir: str, new_prefix: str, classpath: str) -> None:
    if not classpath:
        return ""

    parts = [p.strip() for p in classpath.split(":") if p.strip()]

    rewritten = []
    for p in parts:
        if p == original_dir or p.startswith(original_dir + "/"):
            rewritten.append(p.replace(original_dir, new_prefix, 1))
        else:
            sys.exit(f"Error: Classpath entry '{p}' does not start with original deps dir '{original_dir}'")

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