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

CONTAINER_ENV_FILE = Path("container.env")
OUTPUT_FILE = Path("docker-compose.deps.yml")


def generate_deps_compose(deps_dir: str, container_deps_dir: str) -> None:
    """Generate docker-compose.deps.yml or remove it if inputs are missing."""
    if not deps_dir or not container_deps_dir:
        print("DEPS_DIR or CONTAINER_DEPS_DIR not set — removing deps override file if present.")
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()
        return

    content = f"""services:
  pathcov:
    volumes:
      - {deps_dir}:{container_deps_dir}:ro

  covet-engine:
    volumes:
      - {deps_dir}:{container_deps_dir}:ro
"""

    OUTPUT_FILE.write_text(content)
    print(f"Generated {OUTPUT_FILE}")
    print(f"  Host deps dir: {deps_dir}")
    print(f"  Container mount: {container_deps_dir}")


if __name__ == "__main__":
    # CLI / script usage logic lives only here
    sut_env = dotenv_values("sut.env") if Path("sut.env").exists() else {}
    container_env = dotenv_values(CONTAINER_ENV_FILE) if CONTAINER_ENV_FILE.exists() else {}

    deps_dir = (sut_env.get("DEPS_DIR") or "").strip()
    container_deps_dir = (container_env.get("CONTAINER_DEPS_DIR") or "").strip()

    generate_deps_compose(deps_dir, container_deps_dir)
