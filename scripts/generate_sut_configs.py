#!/usr/bin/env python3
from dotenv import load_dotenv
import os
from pathlib import Path
import yaml

from detect_deps_classpath import detect_build_tool, detect_runtime_deps_classpath, detect_test_deps_classpath, deps_dir_from_build_tool
from rewrite_classpath import rewrite_classpath
from generate_deps_compose import generate_deps_compose

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

test_deps_classpath = None 
# Differentiate between not set and empty
if "test_deps_classpath" in sut_cfg["sut"]:
    test_deps_classpath = "" if not sut_cfg["sut"]["test_deps_classpath"] else sut_cfg["sut"]["test_deps_classpath"]

runtime_deps_classpath = None 
# Differentiate between not set and empty
if "runtime_deps_classpath" in sut_cfg["sut"]:
    runtime_deps_classpath = "" if not sut_cfg["sut"]["runtime_deps_classpath"] else sut_cfg["sut"]["runtime_deps_classpath"]

junit_options = sut_cfg["sut"].get("junit_options", None)

jdart_tests_dir_out = sut_cfg["test_generation"]["generated_tests_dir_out"]

# -------------------------------
# Get the deps classpath
# -------------------------------
load_dotenv(dotenv_path=Path("sut.env"))

sut_dir = os.getenv("SUT_DIR")
if not sut_dir:
    raise RuntimeError("SUT_DIR not set in sut.env")

deps_dir = os.getenv("DEPS_DIR")

load_dotenv(dotenv_path=Path("container.env"))

container_deps_dir = os.getenv("CONTAINER_DEPS_DIR")
if not container_deps_dir:
    raise RuntimeError("CONTAINER_DEPS_DIR not set in container.env")

has_potentially_runtime_deps = runtime_deps_classpath is None or runtime_deps_classpath != ""
has_potentially_test_deps = test_deps_classpath is None or test_deps_classpath != ""

# deps_dir is only necessary if we have potentially dependencies to mount
if not deps_dir and (has_potentially_runtime_deps or has_potentially_test_deps):
    build_tool = detect_build_tool(Path(sut_dir))
    deps_dir = str(deps_dir_from_build_tool(build_tool, Path(sut_dir)))

# Create the mount if necessary
if has_potentially_runtime_deps or has_potentially_test_deps:
    # fail if the deps_dir does not exist
    if not Path(deps_dir).exists():
        raise RuntimeError(f"DEPS_DIR '{deps_dir}' does not exist, but is required to mount dependencies into the container.")

    generate_deps_compose(deps_dir, container_deps_dir)


runtime_deps_cp = None
# Auto-detect classpath
if test_deps_classpath is None:
    raw_runtime_cp = detect_runtime_deps_classpath(sut_dir) if test_deps_classpath is None else test_deps_classpath
    runtime_deps_cp = rewrite_classpath(deps_dir, container_deps_dir, raw_runtime_cp)
# test_deps_classpath override, and it's not empty
elif test_deps_classpath != "":
    runtime_deps_cp = rewrite_classpath(deps_dir, container_deps_dir, test_deps_classpath)

has_runtime_deps = runtime_deps_cp is not None

test_deps_cp = None
# Auto-detect classpath
if test_deps_classpath is None:
    raw_test_cp = detect_test_deps_classpath(sut_dir) if test_deps_classpath is None else test_deps_classpath
    test_deps_cp = rewrite_classpath(deps_dir, container_deps_dir, raw_test_cp)
# test_deps_classpath override, and it's not empty
elif test_deps_classpath != "":
    test_deps_cp = rewrite_classpath(deps_dir, container_deps_dir, test_deps_classpath)

has_test_deps = test_deps_cp is not None

# -------------------------------
# Set the compiled (test) root to absolute paths in container
# -------------------------------
container_sut_dir = os.getenv("CONTAINER_SUT_DIR")
if not container_sut_dir:
    raise RuntimeError("CONTAINER_SUT_DIR not set in container.env")


compiled_root = f"{container_sut_dir}/{compiled_root}"
test_root = f"{container_sut_dir}/{test_root}"
source_root = f"{container_sut_dir}/{source_root}"

# -------------------------------
# Generate Pathcov config
# -------------------------------
pathcov_sig = f"<{cls}: {ret} {method}({param_types})>"

pathcov_cfg = f"""# ============================================================
# SUT configuration (AUTO-GENERATED)
# ============================================================
# Paths should be relative to the root given in the sut.env file

# Compiled classes
COMPILED_ROOT="{compiled_root}"
COMPILED_TEST_ROOT="{test_root}"
SOURCE_PATH="{source_root}"

CLASS_PATH="{compiled_root}{f':{runtime_deps_cp}' if has_runtime_deps else ""}"
TEST_CLASS_PATH="{compiled_root}:{test_root}{f':{test_deps_cp}' if has_test_deps else ""}"

# {"No " if junit_options is None else ""}Junit options
{f'JUNIT_OPTIONS="{junit_options}"' if junit_options is not None else ""}

TARGET_CLASS="{cls}"
FULLY_QUALIFIED_METHOD_SIGNATURE="{pathcov_sig}"
PROJECT_PREFIXES="{project_prefixes}"
"""

pathcov_out = ROOT / "pathcov/configs/sut.config"
pathcov_out.parent.mkdir(parents=True, exist_ok=True)
pathcov_out.write_text(pathcov_cfg)

# -------------------------------
# Generate JDart config
# -------------------------------
jdart_method = f"{cls}.{method}({param_named})"

jdart_cfg = f"""# ============================================================
# AUTO-GENERATED — DO NOT EDIT
# ============================================================
# Compiled classes
classpath={compiled_root}{f':{runtime_deps_cp}' if has_runtime_deps else ""}

# Class under analysis
target={cls}

concolic.method.{method}={jdart_method}
concolic.method={method}

# Generated tests output
jdart.tests.dir={container_sut_dir}/{jdart_tests_dir_out}
"""

jdart_out = ROOT / "jdart/configs/sut_gen.jpf"
jdart_out.parent.mkdir(parents=True, exist_ok=True)
jdart_out.write_text(jdart_cfg)

print("[OK] Generated:")
print(f"  - {pathcov_out}")
print(f"  - {jdart_out}")
