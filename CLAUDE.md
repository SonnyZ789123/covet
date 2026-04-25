# Claude Context and Guidelines

> First take a look at `/Users/yoran.mertens/dev/master-thesis/.claude`. This contains the context about the whole project (CONTEXT.md) and you can **ignore** how to work (HOW_TO_WORK.md).

## Project structure

This repo (`covet`) is the orchestrator for the full test generation pipeline. It does **not** contain the pathcov or covet-engine (forked JDart) Java source code — those live in sibling repos. This project only holds Docker image definitions, shell/Python scripts for orchestration, and configuration templates.

```
.
├── run_pipeline.sh                  # Main entry point — orchestrates the full pipeline
├── container.env                    # Container-side mount paths (/data, /configs, /scripts, /sut, /deps, /output)
├── sut.env                          # Host-side SUT_DIR (and optional DEPS_DIR)
├── configs/
│   └── sut.yml                      # Single canonical SUT specification (target class, method, params, paths)
├── scripts/
│   ├── generate_sut_configs.py      # Reads sut.yml → generates pathcov/configs/sut.config + covet-engine/configs/sut_gen.jpf
│   ├── generate_sut_compose.py      # Generates docker-compose.sut.yml (SUT bind-mount for both containers)
│   ├── generate_deps_compose.py     # Generates docker-compose.deps.yml (dependency JARs bind-mount)
│   ├── detect_deps_classpath.py     # Auto-detects dependency classpath from Maven/Gradle/Ivy/Ant
│   ├── rewrite_classpath.py         # Rewrites host paths to container paths in classpath strings
│   ├── covet_format_classpath.py    # Formats classpath entries for the engine's .jpf config (semicolon-separated, backslash-continued)
│   └── compose_up.sh               # Convenience: starts containers in dev mode without running the pipeline
├── docker-compose.yml               # Base compose: defines pathcov + covet-engine services, pipeline-data volume
├── docker-compose.override.yml      # Dev overrides: bind-mounts local source + shared development/data dir
├── pathcov/
│   ├── Dockerfile                   # Prod image: eclipse-temurin:17 + intellij-coverage-agent + JUnit console + pathcov fat JAR
│   ├── dev/Dockerfile.dev           # Dev image: extends prod, adds SootUp + intellij-coverage-model + pathcov from source (mvn)
│   ├── configs/                     # sut.config is AUTO-GENERATED here (gitignored)
│   └── scripts/
│       ├── run_pipeline.sh          # Entry script (dispatches to dev/ or prod/ based on ENV)
│       ├── common/pipeline_common.sh  # Shared logic: loads sut.config, defines run_junit_with_agent, generate_svg, main_common
│       ├── common/make_coverage_agent_args.sh         # Generates IntelliJ coverage agent config file
│       ├── common/make_intellij_coverage_exporter_config.sh  # Generates coverage exporter JSON config
│       ├── prod/run_pipeline_prod.sh  # Prod: runs pathcov steps via `java -cp $PATHCOV_JAR <MainClass>`
│       └── dev/run_pipeline_dev.sh    # Dev: runs pathcov steps via `mvn exec:java` (from bind-mounted source)
├── covet-engine/                    # Forked JDart (renamed for the COVET pipeline)
│   ├── Dockerfile                   # Image: Ubuntu 14.04 + Java 8 + jpf-core + jConstraints + Z3 4.4.1 + covet-engine
│   └── configs/
│       ├── jdart.jpf                # Default settings for the underlying jdart.* JPF property namespace (CoverageHeuristicStrategy, z3, timeouts, test gen)
│       ├── sut.jpf                  # User-editable: @includes jdart.jpf + sut_gen.jpf. Add custom constraints here.
│       ├── sut_gen.jpf              # AUTO-GENERATED (gitignored): classpath, target, concolic.method
│       └── coverage_heuristic.config  # Points covet-engine to /data/blockmaps/icfg_block_map.json
├── block-diff/
│   ├── Dockerfile                   # Extends pathcov prod image + python3 + block-diff scripts
│   └── scripts/
│       ├── run_block_diff_pipeline.sh  # CI-oriented: checks out 2 commits, generates block maps, diffs, runs tagged tests
│       ├── generate_block_map.sh       # Generates a block map for a single commit
│       ├── generate_block_diff.sh      # Diffs two block maps (added/removed block hashes)
│       ├── generate_include_tags.py    # Converts diff JSON to JUnit --include-tag args
│       └── run_junit_tests.sh          # Runs JUnit with selective tag-based filtering
└── output/                          # Pipeline output dir (coverage graphs, generated tests)
```

### How `run_pipeline.sh` works

1. Sources `container.env` (container-side mount paths) and reads `ENV` (default: `prod`)
2. Runs `scripts/generate_sut_configs.py` — parses `configs/sut.yml` + `sut.env` + `container.env` to generate:
   - `pathcov/configs/sut.config` (shell-sourceable key=value file)
   - `covet-engine/configs/sut_gen.jpf` (JPF properties with classpath, target, concolic.method)
3. Runs `scripts/generate_sut_compose.py` — generates `docker-compose.sut.yml` to bind-mount `SUT_DIR` into both containers at `/sut`
4. `generate_sut_configs.py` also calls `generate_deps_compose.py` if dependencies are detected — generates `docker-compose.deps.yml` to bind-mount the dependency cache (e.g., `~/.m2/repository`) at `/deps`
5. Starts containers via `docker compose` with a layered compose file stack:
   - Always: `docker-compose.yml` (base)
   - If `ENV=dev`: `docker-compose.override.yml` (local source bind-mounts, shared `development/data`)
   - If exists: `docker-compose.sut.yml` (SUT bind-mount)
   - If exists: `docker-compose.deps.yml` (dependency JARs bind-mount)
6. Runs **pathcov stage**: `compose_exec pathcov /scripts/run_pipeline.sh /configs/sut.config /data`
7. Runs **covet-engine stage**: `compose_exec covet-engine /covet-engine-project/jpf-core/bin/jpf /configs/sut.jpf`

### Docker volume architecture

Both containers share a Docker named volume `pipeline-data` mounted at `/data`. The pathcov stage writes the coverage block map to `/data/blockmaps/icfg_block_map.json`, and the covet-engine stage reads it from there (via `coverage_heuristic.config`).

In **dev mode**, the named volume is overridden by a host bind-mount (`./development/data:/data`) so artifacts are visible on the host.

Bind-mounts per container:

| Mount point   | pathcov                          | covet-engine                     |
|---------------|----------------------------------|----------------------------------|
| `/data`       | pipeline-data volume (shared)    | pipeline-data volume (shared)    |
| `/configs`    | `./pathcov/configs` (ro)         | `./covet-engine/configs` (ro)    |
| `/scripts`    | `./pathcov/scripts` (ro)         | —                                |
| `/sut`        | `SUT_DIR` (from sut.env)         | `SUT_DIR` (from sut.env)         |
| `/deps`       | dependency cache (ro, if needed) | dependency cache (ro, if needed) |
| `/output`     | `./output`                       | `./output`                       |

## pathcov pipeline

### Image build (prod — `pathcov/Dockerfile`)

Base: `eclipse-temurin:17-jdk`. Installs graphviz (for SVG rendering). Downloads three JARs:
- **IntelliJ Coverage Agent** (`intellij-coverage-agent-1.0.771.jar`) — Java agent for runtime coverage instrumentation
- **JUnit Platform Console Standalone** (`junit-platform-console-standalone-1.12.2.jar`) — runs JUnit tests headlessly
- **pathcov fat JAR** (`pathcov-<version>.jar`) — shaded JAR from GitHub Releases containing pathcov + SootUp + intellij-coverage-model

The prod image contains no source code — just pre-built JARs. The image tag is `sonnyz789123/pathcov-image:<version>`.

### Image build (dev — `pathcov/dev/Dockerfile.dev`)

Extends the prod image (`sonnyz789123/pathcov-image:latest`). Adds maven + git, then builds from source:
1. Clones and `mvn install`s **SootUp** (forked, v2.0.1) — static analysis framework for generating CFGs/ICFGs and call graphs
2. Clones and `mvn install`s **intellij-coverage-model** (v3.0.1) — shared DTO for coverage data (also used by covet-engine)
3. Clones **pathcov** and builds with `-DskipShade` (keeps dependencies separate, not fat JAR)
4. Overrides `PATHCOV_JAR` env var to point to the thin JAR

In dev mode, `docker-compose.override.yml` bind-mounts the local pathcov source (`../pathcov`) over `/pathcov-project/pathcov`, so you can edit and re-run without rebuilding the image. Dev scripts use `mvn exec:java` instead of `java -cp`.

### Pipeline execution steps

The pathcov container runs `run_pipeline.sh` which dispatches to `run_pipeline_prod.sh` or `run_pipeline_dev.sh` based on `ENV`. Both follow the same `main_common` sequence defined in `pipeline_common.sh`:

1. **`write_cg_classes`** — Uses SootUp to generate the call graph from the target method signature, filtered by `project_prefixes`. Outputs a list of classes to `$DATA_DIR/intellij-coverage/cg_classes.txt`. This scopes the coverage analysis.

2. **`run_junit_with_agent`** — Runs the existing test suite via JUnit Platform Console with the IntelliJ Coverage Agent attached as a `-javaagent`. The agent instruments bytecode at runtime and writes binary coverage data to `$DATA_DIR/intellij-coverage/intellij_coverage_report.ic`. Only classes from the CG classes list are instrumented.

3. **`generate_coverage_data`** — Runs pathcov's `CoverageExportMain` which reads the binary `.ic` report and exports it as JSON to `$DATA_DIR/coverage/coverage_data.json`. Uses a generated config that specifies output roots, source roots, and included classes.

4. **`generate_block_map`** — Runs pathcov's `GenerateBlockMap` which uses SootUp to build the interprocedural CFG of the target method, then maps coverage data (line-level) onto CFG blocks. Each block gets a structural hash. Outputs `$DATA_DIR/blockmaps/icfg_block_map.json`. **This is the key artifact** — covet-engine reads this to guide exploration.

5. **`generate_coverage_graph`** — Runs pathcov's `GenerateCoverageGraph` which renders the ICFG as a Graphviz `.dot` file with blocks colored green (fully covered), yellow (partially covered), or red (uncovered).

6. **`calculate_branch_coverage`** — Computes and prints the branch coverage percentage from the block map.

7. **`generate_svg`** — Converts the `.dot` file to SVG via graphviz `dot` (10s timeout).

### Key environment variables (set in Dockerfile/docker-compose)

- `PATHCOV_JAR` — path to the pathcov JAR (fat in prod, thin in dev)
- `INTELLIJ_COVERAGE_AGENT_JAR` — path to the IntelliJ coverage agent JAR
- `JUNIT_CONSOLE_JAR` — path to the JUnit Console Standalone JAR
- `PATHCOV_PROJECT_DIR` — (dev only) `/pathcov-project`, root for all source builds

## covet-engine pipeline (forked JDart)

### Image build (`covet-engine/Dockerfile`)

Base: `ubuntu:14.04` (required for Java 8 / Z3 4.4.1 compatibility). Platform: `linux/amd64` (forced in docker-compose.yml for Apple Silicon compatibility).

Build steps:
1. Installs **OpenJDK 8**, ant, maven, git, build tools
2. Clones and builds **jpf-core** (Java PathFinder, tag `JPF-8.0`) with `ant` — the bytecode VM that the engine runs on top of
3. Clones and `mvn install`s **jConstraints** — constraint abstraction layer
4. Downloads **Z3 4.4.1** (SMT solver binary for Ubuntu 14.04), installs its Java binding JAR into local Maven repo
5. Clones and `mvn install`s **jconstraints-z3** — Z3 backend for jConstraints
6. Configures JPF: writes `/root/.jpf/site.properties` with `jpf-core` and `jpf-jdart` keys (the `jpf-jdart` key is upstream JPF convention; its value points to `${COVET_DIR}/covet-engine`)
7. Configures jConstraints: copies z3 JARs into `/root/.jconstraints/extensions/`
8. Clones **covet-engine** (forked JDart, from `SonnyZ789123/covet-engine`) and builds with `ant`

The image tag is `sonnyz789123/covet-engine-image:<version>`. The engine has no build manager — it uses ant and manual classpath management (inherited from upstream JDart).

### How covet-engine is invoked

From `run_pipeline.sh`:
```bash
compose_exec covet-engine /covet-engine-project/jpf-core/bin/jpf /configs/sut.jpf
```

The `jpf` launcher script starts Java PathFinder with the given config file. JPF loads the engine as a shell plugin (via the `gov.nasa.jpf.jdart.JDart` shell class — upstream package name retained).

### Config chain

`sut.jpf` (user-editable, bind-mounted at `/configs/sut.jpf`) includes:
1. **`jdart.jpf`** — Default settings for the upstream `jdart.*` JPF property namespace:
   - `shell=gov.nasa.jpf.jdart.JDart` (loads the engine as the JPF shell)
   - `symbolic.dp=z3` with bitvectors enabled
   - `jdart.exploration=CoverageHeuristicStrategy(/configs/coverage_heuristic.config)` (coverage-guided exploration, the main thesis contribution)
   - `jdart.tests.gen=true` (enable test suite generation)
   - `jdart.termination=TimedTermination,0,0,30` (30 second timeout)
   - `z3.timeout=5000` (5 second constraint solver timeout)
2. **`sut_gen.jpf`** — Auto-generated by `generate_sut_configs.py`:
   - `classpath=` — compiled classes + runtime dependencies (semicolon-separated)
   - `target=` — entry class (the class containing `main` or the test wrapper)
   - `concolic.method.<name>=` — fully qualified method with named typed params (e.g., `Class.method(x:int,y:int)`)
   - `jdart.tests.dir=` — output directory for generated test files

**`coverage_heuristic.config`** tells the engine where to find the block map produced by pathcov:
- `jdart.exploration.coverage_heuristic.coverage_data_path=/data/blockmaps/icfg_block_map.json`
- `jdart.exploration.coverage_heuristic.ignore_covered_paths=true` — marks fully-covered paths as `IGNORE`

### What covet-engine produces

- Explores execution paths of the target method via concolic execution on JPF's bytecode VM
- The CoverageHeuristicStrategy reads the block map to prioritize uncovered/partially-covered CFG nodes and skip already-covered paths
- For each path: records result state (OK, ERROR, DONT_KNOW, IGNORE) and the concrete input valuations
- The test suite generator creates JUnit test files (JUnit 4 or 5) with `assertEquals` for OK paths and `assertThrows` for ERROR paths
- Generated tests are written to the configured output directory (default: `/output/generated-tests` or a custom path in the SUT)

### Dev mode for covet-engine

In dev mode, `docker-compose.override.yml` bind-mounts the local covet-engine source (`../covet-engine/`) over `/covet-engine-project/covet-engine`. To recompile after changes, exec into the container and run `ant`:
```bash
docker exec -it covet-engine /bin/bash
cd /covet-engine-project/covet-engine && ant
```
This is necessary because the host machine likely has JDK 21+, but the engine requires JDK 8.