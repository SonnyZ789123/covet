#!/usr/bin/env python3
from dotenv import load_dotenv
import os
from pathlib import Path
import yaml

from detect_deps_classpath import detect_build_tool, detect_deps_classpath, deps_dir_from_build_tool
from rewrite_classpath import rewrite_classpath

ROOT = Path(__file__).resolve().parents[1]

sut_cfg = yaml.safe_load((ROOT / "configs/sut.yml").read_text())

# -------------------------------
# Extract canonical information
# -------------------------------
cls = sut_cfg["target"]["class"]
method = sut_cfg["target"]["method"]
ret = sut_cfg["target"]["return"]

params = sut_cfg["target"]["parameters"]
param_types = ",".join(p["type"] for p in params)
param_named = ",".join(f'{p["name"]}:{p["type"]}' for p in params)

project_prefixes = ",".join(sut_cfg["analysis"]["project_prefixes"])

compiled_root = sut_cfg["sut"]["compiled_root"]
test_root = sut_cfg["sut"]["test_root"]
source_root = sut_cfg["sut"]["source_root"]
deps_class_path = None 
# Differentiate between not set and empty
if "deps_class_path" in sut_cfg["sut"]:
    print(f"Using deps_class_path from sut.yml")
    deps_class_path = "" if not sut_cfg["sut"]["deps_class_path"] else sut_cfg["sut"]["deps_class_path"]
jdart_tests_dir_out = sut_cfg["test_generation"]["generated_tests_dir_out"]

# -------------------------------
# Get the deps classpath
# -------------------------------
load_dotenv(dotenv_path=Path(".env"))

sut_dir = os.getenv("SUT_DIR")

if not sut_dir:
    raise RuntimeError("SUT_DIR not set in .env")

deps_dir = os.getenv("DEPS_DIR")

if not deps_dir and (deps_class_path is None or deps_class_path != ""):
    build_tool = detect_build_tool(Path(sut_dir))
    deps_dir = str(deps_dir_from_build_tool(build_tool, Path(sut_dir))) 

# TODO: make shared constant more explicit between here and the Dockerfile
CONTAINER_REPO = "/dependencies"

deps_cp = None
# Auto-detect classpath
if deps_class_path is None:
    raw_cp = detect_deps_classpath(sut_dir) if deps_class_path is None else deps_class_path
    deps_cp = rewrite_classpath(deps_dir, CONTAINER_REPO, raw_cp)
# deps_class_path override, and it's not empty
elif deps_class_path != "":
    deps_cp = rewrite_classpath(deps_dir, CONTAINER_REPO, deps_class_path)

has_deps = deps_cp is not None

# -------------------------------
# Generate Pathcov config
# -------------------------------
pathcov_sig = f"<{cls}: {ret} {method}({param_types})>"

pathcov_cfg = f"""# ============================================================
# SUT configuration (AUTO-GENERATED)
# ============================================================
# Paths should be relative to the root given in the .env file

# Compiled classes
CLASS_PATH="{compiled_root}"
TEST_CLASS_PATH="{test_root}"
SOURCE_PATH="{source_root}"

# {"No " if not has_deps else ""}Dependencies
{f'DEPS_CLASS_PATH="{deps_cp}"' if has_deps else ""}

TARGET_CLASS="{cls}"
FULLY_QUALIFIED_METHOD_SIGNATURE="{pathcov_sig}"
PROJECT_PREFIXES="{project_prefixes}"
"""

pathcov_out = ROOT / "pathcov/configs/sut.config"
pathcov_out.parent.mkdir(parents=True, exist_ok=True)   # ← FIX
pathcov_out.write_text(pathcov_cfg)

# -------------------------------
# Generate JDart config
# -------------------------------
jdart_method = f"{cls}.{method}({param_named})"

jdart_cfg = f"""# ============================================================
# AUTO-GENERATED — DO NOT EDIT
# ============================================================
# Compiled classes
classpath=/sut/{compiled_root}

# Class under analysis
target={cls}

concolic.method.{method}={jdart_method}
concolic.method={method}

# Generated tests output
jdart.tests.dir=/sut/{jdart_tests_dir_out}
"""

jdart_out = ROOT / "jdart/configs/sut_gen.jpf"
jdart_out.parent.mkdir(parents=True, exist_ok=True)      # ← FIX
jdart_out.write_text(jdart_cfg)

print("[OK] Generated:")
print(f"  - {pathcov_out}")
print(f"  - {jdart_out}")
