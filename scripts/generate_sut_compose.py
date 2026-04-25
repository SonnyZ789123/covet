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

from pathlib import Path
from dotenv import dotenv_values

SUT_ENV_FILE = Path("sut.env")
CONTAINER_ENV_FILE = Path("container.env")
OUTPUT_FILE = Path("docker-compose.sut.yml")


def main():
    sut_env = dotenv_values(SUT_ENV_FILE) if SUT_ENV_FILE.exists() else {}
    container_env = dotenv_values(CONTAINER_ENV_FILE) if CONTAINER_ENV_FILE.exists() else {}

    sut_dir = (sut_env.get("SUT_DIR") or "").strip()
    container_sut_dir = (container_env.get("CONTAINER_SUT_DIR") or "").strip()

    if not sut_dir or not container_sut_dir:
        print("SUT_DIR or CONTAINER_SUT_DIR not set — removing sut override file if present.")
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()
        return

    content = f"""services:
  pathcov:
    volumes:
      - {sut_dir}:{container_sut_dir}

  covet-engine:
    volumes:
      - {sut_dir}:{container_sut_dir}
"""

    OUTPUT_FILE.write_text(content)
    print(f"Generated {OUTPUT_FILE}")
    print(f"  Host SUT dir: {sut_dir}")
    print(f"  Container mount: {container_sut_dir}")


if __name__ == "__main__":
    main()
