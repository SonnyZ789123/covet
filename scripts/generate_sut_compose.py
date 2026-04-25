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
