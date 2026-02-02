#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Command '{' '.join(cmd)}' failed with exit code {result.returncode}")
    return result.stdout.strip()


def detect_build_tool(project_dir: Path):
    if (project_dir / "pom.xml").exists():
        return "maven"
    if (project_dir / "build.gradle").exists() or (project_dir / "build.gradle.kts").exists():
        return "gradle"
    if (project_dir / "ivy.xml").exists():
        return "ivy"
    if (project_dir / "build.xml").exists():
        return "ant"
    return None


def deps_dir_from_build_tool(build_tool: str, project_dir: Path) -> Path:
    if not build_tool: 
        raise RuntimeError("Could not detect build tool (Maven, Gradle, Ivy/Ant), please set deps_class_path and DEPS_DIR manually")

    home = Path.home()

    if build_tool == "maven":
        # Default local Maven repository
        return home / ".m2" / "repository"

    if build_tool == "gradle":
        # Gradle dependency cache (artifacts live under modules-2/files-2.1)
        return home / ".gradle" / "caches" / "modules-2" / "files-2.1"

    if build_tool == "ivy":
        # Ivy default cache location
        return home / ".ivy2" / "cache"

    if build_tool == "ant":
        # Ant itself has no dependency manager.
        # Common patterns:
        #  1) Uses Ivy → ~/.ivy2/cache
        #  2) Project-local lib/ directory
        ivy_cache = home / ".ivy2" / "cache"
        if ivy_cache.exists():
            return ivy_cache

        project_lib = project_dir / "lib"
        if project_lib.exists():
            return project_lib

        # Fallback: current project dir (last resort)
        return project_dir

    raise RuntimeError(f"Build tool '{build_tool}' not supported for deps dir detection")


# ============================================================
# MAVEN
# ============================================================

def maven_classpath_with_scope(project_dir: Path, scope: str):
    tmp_file = project_dir / f".classpath.{scope}.tmp"
    cmd = [
        "mvn", "-q",
        "-Dmdep.outputAbsoluteArtifactFilename=true",
        "-Dmdep.pathSeparator=:",
        f"-Dmdep.outputFile={tmp_file}",
        f"-DincludeScope={scope}",
        "dependency:build-classpath"
    ]
    run(cmd, project_dir)
    cp = tmp_file.read_text().strip() if tmp_file.exists() else ""
    tmp_file.unlink(missing_ok=True)
    return cp


def maven_test_deps_classpath(project_dir: Path):
    return maven_classpath_with_scope(project_dir, "test")


def maven_runtime_deps_classpath(project_dir: Path):
    return maven_classpath_with_scope(project_dir, "runtime")


# ============================================================
# GRADLE
# ============================================================

def gradle_test_deps_classpath(project_dir: Path):
    init_script = project_dir / ".print_classpath.gradle"
    init_script.write_text("""
allprojects {
    afterEvaluate { project ->
        if (project.plugins.hasPlugin('java')) {
            project.tasks.register("printAllDepsClasspath") {
                doLast {
                    def cp = []
                    if (project.sourceSets.findByName("main")) {
                        cp += project.sourceSets.main.runtimeClasspath.files
                    }
                    if (project.sourceSets.findByName("test")) {
                        cp += project.sourceSets.test.runtimeClasspath.files
                    }
                    println cp.collect { it.absolutePath }.unique().join(":")
                }
            }
        }
    }
}
""")
    cmd = ["gradle", "-q", "--init-script", str(init_script), "printAllDepsClasspath"]
    cp = run(cmd, project_dir)
    init_script.unlink(missing_ok=True)
    return cp


def gradle_runtime_deps_classpath(project_dir: Path):
    init_script = project_dir / ".print_runtime_classpath.gradle"
    init_script.write_text("""
allprojects {
    afterEvaluate { project ->
        if (project.plugins.hasPlugin('java')) {
            project.tasks.register("printRuntimeDepsClasspath") {
                doLast {
                    def runtimeCp = project.sourceSets.main.runtimeClasspath.files
                        .collect { it.absolutePath }
                        .unique()
                        .join(":")
                    println runtimeCp
                }
            }
        }
    }
}
""")

    runtime_cp = run(
        ["gradle", "-q", "--init-script", str(init_script), "printRuntimeDepsClasspath"],
        project_dir
    )

    init_script.unlink(missing_ok=True)
    return runtime_cp.strip()


# ============================================================
# IVY / ANT
# ============================================================

def ivy_resolve(project_dir: Path, conf: str):
    cmd = ["ant", "-q", f"-Divy.conf={conf}", "resolve", "retrieve"]
    run(cmd, project_dir)

    jars = list(project_dir.rglob("*.jar"))
    return ":".join(str(j.resolve()) for j in jars)


def ivy_test_deps_classpath(project_dir: Path):
    return ivy_resolve(project_dir, "test")


def ivy_runtime_deps_classpath(project_dir: Path):
    return ivy_resolve(project_dir, "runtime")


# ============================================================
# PUBLIC API
# ============================================================

def detect_test_deps_classpath(project_dir_str: str):
    project_dir = Path(project_dir_str).resolve()
    tool = detect_build_tool(project_dir)

    if tool == "maven":
        return maven_test_deps_classpath(project_dir)
    elif tool == "gradle":
        return gradle_test_deps_classpath(project_dir)
    elif tool in ("ivy", "ant"):
        return ivy_test_deps_classpath(project_dir)
    else:
        raise RuntimeError("Unsupported build tool")


def detect_runtime_deps_classpath(project_dir_str: str):
    project_dir = Path(project_dir_str).resolve()
    tool = detect_build_tool(project_dir)

    if tool == "maven":
        return maven_runtime_deps_classpath(project_dir)
    elif tool == "gradle":
        return gradle_runtime_deps_classpath(project_dir)
    elif tool in ("ivy", "ant"):
        return ivy_runtime_deps_classpath(project_dir)
    else:
        raise RuntimeError("Unsupported build tool")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  detect_classpath.py <project_dir>")
        sys.exit(1)

    project_dir = sys.argv[1]

    runtime_cp = detect_runtime_deps_classpath(project_dir)
    test_cp = detect_test_deps_classpath(project_dir)
    print("=== RUNTIME DEPENDENCIES ===")
    print(runtime_cp)
    print("\n=== TEST DEPENDENCIES ===")
    print(test_cp)
