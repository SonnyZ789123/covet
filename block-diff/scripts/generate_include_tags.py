#!/usr/bin/env python3
import json
import sys


def build_include_tag_string(data):
    tags = []
    tags.extend(data.get("addedBlockHashes", []))
    tags.extend(data.get("removedBlockHashes", []))

    # No changed blocks => no tags => caller should skip tests
    if not tags:
        return ""

    # Emit: --include-tag TAG1 --include-tag TAG2 ...
    return " ".join(arg for tag in tags for arg in ("--include-tag", tag))


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    print(build_include_tag_string(data))


if __name__ == "__main__":
    main()
