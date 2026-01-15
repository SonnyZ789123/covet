#!/usr/bin/env python3
from pathlib import Path
import yaml

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
jdart_tests_dir_out = sut_cfg["test_generation"]["generated_tests_dir_out"]

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
