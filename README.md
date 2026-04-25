# Coverage-Guided Concolic Pipeline

An end-to-end, containerized pipeline for **coverage-guided concolic test generation** in Java.
This project integrates **static CFG/ICFG analysis**, **runtime coverage instrumentation**, **coverage graph construction**, and **heuristic-guided concolic execution with covet-engine (forked JDart)** to systematically discover uncovered execution paths.

The pipeline is designed to be **reproducible**, **configurable**, and **tool-agnostic**, with a single SUT specification.

## Overview

The pipeline consists of two main stages:

1. **Pathcov stage**
   * Generates block maps (CFG/ICFG)
   * Runs the existing test suite with a custom the IntelliJ Coverage Agent
   * Extracts line and branch coverage
   * Builds coverage graphs

2. **covet-engine stage** (forked JDart)
   * Uses coverage information to guide concolic execution
   * Explores uncovered and partially covered execution paths
   * Generates new JUnit test cases to cover those paths

All stages are fully containerized and orchestrated via Docker Compose.


## Repository Structure

```
.
├── configs
│   └── sut.yml                   # Canonical SUT specification
├── docker-compose.yml            # Orchestrates Pathcov and covet-engine containers
├── development
│   └── data                      # Developmnet: bind-mount for output 
├── covet-engine                  # Forked JDart, packaged as the COVET concolic engine
│   ├── Dockerfile
│   └── configs
│       ├── jdart.jpf             # Defaults for the upstream jdart.* JPF property namespace
│       ├── sut.jpf               # Base config (user-editable)
│       ├── sut_gen.jpf           # AUTO-GENERATED from sut.yml
│       └── coverage_heuristic.config
├── pathcov
│   ├── Dockerfile
│   ├── configs
│   │   └── sut.config            # AUTO-GENERATED from sut.yml
│   └── scripts
│       └── run_pathcov_pipeline.sh
├── scripts
│   └── generate_sut_configs.py   # Generates tool-specific configs from sut.yml
├── run_pipeline.sh               # Main script for running the pipeline
└── requirements.txt              # Host-side Python dependencies
```

## Requirements (Host)

* Docker
* Docker Compose
* Python ≥ 3.8
* PyYAML

Install the Python dependency once:

```bash
python3 -m pip install -r requirements.txt
```

## Step 1: Configure the SUT directory (`.env`)

The System Under Test (SUT) must be available on the host and mounted into both containers.

Create a `.env` file in the repository root:

```bash
SUT_DIR=$HOME/dev/jdart-examples
```

Requirements for `SUT_DIR`:

* It must contain **compiled class files**
* It must contain **compiled test files**
* It must contain **source files**
* The directory will be mounted into containers at `/sut`

Example inside the container:

```
/sut/out/production/jdart-examples
/sut/out/test/jdart-examples
```

> **Note**
> `.env` is automatically read by Docker Compose.
> It is also explicitly loaded by `run_pipeline.sh` so that host-side scripts see the same variables.

## Step 2: Define the SUT and target method (`configs/sut.yml`)

`sut.yml` is the **single canonical configuration** that defines:

* where class and source files live
* which method is analyzed
* where generated tests should be written

Example:

```yaml
sut:
  compiled_root: out/production/jdart-examples
  test_root: out/test/jdart-examples
  source_root: src/main/java

test_generation:
  generated_tests_dir_out: data/generated-tests

target:
  class: test.testsuites.Test
  method: bar
  return: int
  parameters:
    - name: a
      type: int

analysis:
  project_prefixes: # optional 
    - test.testsuites 
```

You only edit **this file** to change the SUT or the analyzed method.

All tool-specific configurations are **derived automatically** from this file.

## Step 3: (Optional) Configure covet-engine behavior

You may customize engine-specific options in:

```
covet-engine/configs/sut.jpf
```

This file is **not generated** and is intended for manual tuning.

### Examples of useful engine options

Enable fine-grained logging:

```properties
log.finest=jdart,jdart.testsuites
```

Enable test generation:

```properties
jdart.tests.gen=true
```

Select a custom exploration strategy:

```properties
# Coverage guided (this is the default and will use coverage information of the pathcov step)
jdart.exploration=gov.nasa.jpf.jdart.exploration.CoverageHeuristicStrategy(/configs/coverage_heuristic.config)

# Depth First
jdart.exploration=gov.nasa.jpf.jdart.exploration.DFSStrategy

# Breadth First
jdart.exploration=gov.nasa.jpf.jdart.exploration.BFSStrategy
```

Stop exploration once a target branch coverage is reached:

```properties
# Stop when runtime branch coverage (initial test suite + JDart discoveries)
# reaches 80%. Requires a coverage tracker -- automatic with the coverage
# heuristic, or via jdart.coverage.block_map_path for DFS/BFS (see below).
jdart.termination=gov.nasa.jpf.jdart.termination.BranchCoverageTermination,80
```

Enable coverage telemetry and IGNORE filtering for any exploration strategy:

```properties
# Path to the block map JSON produced by the pathcov stage. Required for
# DFS/BFS to get coverage telemetry, BranchCoverageTermination, and
# IGNORE filtering. The coverage heuristic loads this automatically from
# coverage_heuristic.config -- no need to set it there.
jdart.coverage.block_map_path=/data/blockmaps/icfg_block_map.json

# Mark paths whose branches are all already covered as IGNORE. Off by
# default for DFS/BFS (every path is kept for fair strategy comparison).
jdart.coverage.ignore_covered_paths=true
```

When a coverage tracker is available, covet-engine emits an `elapsed=Xms branch_coverage=Y%`
line on the `jdart.evaluation` logger every time branch coverage changes:

```properties
log.info=jdart.evaluation,jdart
```

During execution, this file is **combined** with the auto-generated covet-engine configuration (`sut_gen.jpf`).

Full `sut.jpf` configuration example:
```
# enable test genration
jdart.tests.gen=true

# set the configId for other settings (jdart.configs.<configId>.<setting>)
concolic.method.foo.config=foo

# add constraints to the input parameters d1 and d2
jdart.configs.foo.constraints=(d1 > 0.0 && d2 > 0.0)

# max node depth in the execution tree
jdart.configs.foo.max_depth=100

# max nested calls
jdart.configs.foo.max_nesting_depth=5

# max times the solver tries to find a valuation to reach a certain node
jdart.configs.foo.max_alt_depth=1

# switch to a DFS exploration strategy
jdart.exploration=gov.nasa.jpf.jdart.exploration.DFSStrategy

# enable coverage telemetry / termination / IGNORE for DFS or BFS
jdart.coverage.block_map_path=/data/blockmaps/icfg_block_map.json
jdart.coverage.ignore_covered_paths=true

# Stop the concolic execution after 5 seconds
jdart.termination=gov.nasa.jpf.jdart.termination.TimedTermination,0,0,5

# Stop once runtime branch coverage reaches 80%
jdart.termination=gov.nasa.jpf.jdart.termination.BranchCoverageTermination,80

# Stop the constraint solver (invoked to find a new path) after 1 second
z3.timeout=1000

# The classname of the generated test file, ideally ending with "Test" (JUnit5)
jdart.tests.suitename=CustomSuiteNameTest

# The out dir for the generated test suite (default set to data/generated-tests of your sut dir)
# Note that covet-engine runs in a container where the sut is bind-mounted to /sut
jdart.tests.dir=/sut/other-data-dir/tests

# The package name of the test suite (default set to the package of the method under test) 
jdart.tests.pkg=com.other.package

# Enable/disable logging
# log_level can be set to info, warning, fine, finer, finest, severe
# default is 
#		log.finest=jdart,jdart.testsuites
#   log.info=constraints
log.<log_level>=jdart,jdart.debug,jdart.testsuites

# Manually add classpaths of external libraries
classpath+=:/sut/data/libraries/jdart-examples-library-dep-1.0-SNAPSHOT.jar
```

## Step 4: Run the pipeline

Once everything is configured, run:

```bash
./run_pipeline.sh
```

This command will:

1. Generate tool-specific configs from `configs/sut.yml`
2. Start the Docker containers
3. Run the Pathcov stage
4. Run covet-engine with the generated configuration

No manual Docker commands are required.

## Generated Artifacts

All process data is written to a shared Docker volume mounted at:

```
/data
```

This includes:

* coverage data
* coverage graphs (`.dot`, `.svg`)

The volume persists across container runs.

The test suite is genereted in the SUT directory, specified in the `sut.yml`. 

## Development Mode (Optional)

By default, the pipeline runs in **production mode**, using **pre-built Docker images**.

For development (e.g. modifying Pathcov or the coverage agent locally), you can enable **development mode** using a Docker Compose override file.

### docker-compose.override.yml

Create a `docker-compose.override.yml` file and bind-mount your locally cloned tools:

```yaml
services:
  pathcov:
    environment:
      - ENV=dev

    volumes:
      - ./development/data:/data
      - ../pathcov:/pathcov-project/pathcov

  covet-engine:
    environment:
      - ENV=dev

    volumes:
      - ./development/data:/data
      - ../covet-engine:/covet-engine-project/covet-engine
```

It is important that the /data mouts between the pathcov and the covet-engine service are the same.

In your `.env` file, set `ENV=dev` and run the pipeline.

* `docker-compose.override.yml` is automatically applied by Docker Compose
* Production images remain unchanged
* You can override:
  * tool source directories
  * JAR locations
  * other environment variables as needed

No script changes are required.

## Docker Architecture

### Docker Compose

* **pathcov container**
  * Runs coverage instrumentation and graph generation
  * Mounts:
    * `/sut` (SUT)
    * `/configs` (Pathcov configs)
    * `/scripts` (Pathcov scripts)
    * `/data` (shared artifacts)
* **covet-engine container**
  * Runs covet-engine (forked JDart) on JPF
  * Mounts:
    * `/sut` (SUT)
    * `/configs` (covet-engine configs)
    * `/data` (shared artifacts)

Containers do **not** communicate directly.
The host orchestrates execution via `run_pipeline.sh`.

## Typical Workflow

```bash
git clone <repo>
cd coverage-guided-concolic-pipeline

python3 -m pip install -r requirements.txt

cat <<EOF > .env
ENV=dev
SUT_DIR=$HOME/dev/your-sut-directory
EOF

vim configs/sut.yml
vim covet-engine/configs/sut.jpf   # optional

./run_pipeline.sh

```

## How to see the coverage graph 

In production mode, the coverage graph is generated in a Docker volume. To easily see the coverage graph, run the pipeline in development mode by setting `ENV=dev` in your `.env` file. Specify a bind-mount to your output folder in the `docker-compose.override.yml` file: 

```yaml
services:
  pathcov:
    environment:
      - ENV=dev

    volumes:
      - ./development/data:/data

  covet-engine:
    environment:
      - ENV=dev

    volumes:
      - ./development/data:/data
```

After running the pipeline, which runs `scripts/run_pathcov_pipeline.sh` in the pathcov-container, a `coverage_graph.svg` file is created in the specified /data folder with path `/data/visualization/icfg/coverage/coverage_graph.svg`.

Then just execute `open data/visualization/icfg/coverage/coverage_graph.svg`. 

### See coverage graph after test suite generation

After running the pipeline with `jdart.tests.gen=true`, copy-paste the test file(s) in the corresponding tests package. Go into the pathcov-container by runnning: 

```bash
docker exec -it pathcov bash
```

And execute the `run_pathcov_pipeline.sh` script again by executing: 

```bash
/scripts/run_pathcov_pipeline.sh
```

Then open the `coverage_graph.svg` again as explained above. 

## About JDart execution 

### What JDart Is For

JDart performs **concolic execution** of Java methods to explore **full execution paths** and generate JUnit tests. It is intended for **small, bounded, single-threaded methods** driven by **primitive inputs**.

### Symbolic vs Concrete

**Symbolic**

- Only **primitive data types** can become symbolic
- `int`, `long`, `short`, `byte`, `char`, `boolean`, `float`, `double`
- This includes primitive fields of objects
- The elements of a primitive data type array `PrimitiveType[]` can become symbolic, but the array itself stays concrete

**Always Concrete**

- Non-primitive data types
- `String`, user defined classes, arrays

Only symbolic parameters can induce to-be-explored branches.

### What is explored

- Control flow: `if–else`, nested conditionals, `switch`, short-circuit logic
- Interprocedural calls with symbolic propagation
- `throw`, runtime exceptions, `try–catch`
- Division by zero is explicitly branched
- JDart supports multiple exploration strategies, and constraint solver is interchangeable (default is z3)

### Unsupported (yet) / Limited Features

- **Recursion is unsupported**
- **Concurrency is unsupported** (single-threaded only)
- **Usage of external libraries are unsupported during test suite generation**
- Unbounded or unchecked loops can cause infinite loop expansion
- Loops with symbols can cause path explosion
- Multi-dimensional arrays, arrays of objects stay concrete

### Loops

- Loops are **bytecode-level unrolled**
- Symbolic loop conditions → path explosion
- Unbounded loops can be controlled via config defined constraints

### Test Generation

Generated tests:
- Cover **only full paths**
- Assert **only return values**
- Do **not** check side effects, invariants, or post-conditions
- Paths marked `DONT_KNOW` or `IGNORE` are skipped
- The exploration strategy `CoverageHeuristicStrategy` marks already covered paths with `IGNORE`, which essentially makes the test suite generator create test cases only for uncovered paths

### Determinism

- Execution is deterministic under JPF
- Time, randomness, and object identity are fixed, even for external libraries
- True non-determinism only via uninstrumented external calls (networked calls for example)

### Summary

**JDart works best for**

- Small, primitive-centric methods
- Bounded exploration
- Academic and controlled benchmarks

**JDart is not suited for**

- Recursive or concurrent code
- Heap-heavy or library-intensive applications

## License

See `LICENSE`.
