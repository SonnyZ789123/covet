#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
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
        sys.exit("Could not detect build tool (Maven, Gradle, Ivy/Ant), please set deps_class_path and DEPS_DIR manually")

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

    sys.exit(f"Build tool '{build_tool}' not supported for deps dir detection")


# ---------- MAVEN (compile + runtime + test) ----------
def maven_classpath(project_dir: Path):
    tmp_file = project_dir / ".classpath.tmp"
    cmd = [
        "mvn", "-q",
        "-Dmdep.outputAbsoluteArtifactFilename=true",
        "-Dmdep.pathSeparator=:",
        f"-Dmdep.outputFile={tmp_file}",
        "-DincludeScope=test",  # <-- THIS pulls everything
        "dependency:build-classpath"
    ]
    run(cmd, project_dir)
    cp = tmp_file.read_text().strip()
    tmp_file.unlink(missing_ok=True)
    return cp


# ---------- GRADLE (main + test runtime) ----------
def gradle_classpath(project_dir: Path):
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


# ---------- IVY (resolve everything, grab jars) ----------
def ivy_classpath(project_dir: Path):
    cmd = ["ant", "-q", "resolve", "retrieve"]
    run(cmd, project_dir)

    jars = list(project_dir.rglob("*.jar"))
    return ":".join(str(j.resolve()) for j in jars)


def detect_deps_classpath(project_dir_str: str):
    project_dir = Path(project_dir_str).resolve()
    if not project_dir.exists():
        sys.exit("Project directory does not exist")

    tool = detect_build_tool(project_dir)
    if not tool:
        sys.exit("Could not detect build tool (Maven, Gradle, Ivy/Ant)")

    if tool == "maven":
        cp = maven_classpath(project_dir)
    elif tool == "gradle":
        cp = gradle_classpath(project_dir)
    elif tool == "ivy":
        cp = ivy_classpath(project_dir)
    else:
        sys.exit(f"Build tool '{tool}' detected but not supported for dependency extraction")

    return cp


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: detect_classpath.py <project_dir>")
        sys.exit(1)

    cp = detect_deps_classpath(sys.argv[1])
    print(cp)