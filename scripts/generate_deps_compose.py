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

  jdart:
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
