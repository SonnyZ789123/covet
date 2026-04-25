# Test Suite Generation Example

## 1. Get the required tooling

Clone this repository: 
```bash
git clone https://github.com/SonnyZ789123/covet.git
```

Clone the repository holding the example program:
```bash
git clone https://github.com/SonnyZ789123/jdart-examples.git
```

This exapmle program (in the class `OverallJDartExample`) already has a test suite that partially tests some paths. 

## 2. Build the jdart-examples project

In the jdart-examples directory, build the project. It is a simple project that solely uses the IntelliJ build tools. You'll have to build by opening the project in the IntelliJ IDEA, then in the toolbar, go to "build", then click on "Build Project". Or just use the shortcut `cmd + f9`. 

Create a `.env` file and point `SUT_DIR` to the directory containing the project and set the environment to `dev`. 

```env
ENV=dev
SUT_DIR=$HOME/dev/jdart-examples
```

## 3. Set the SUT configuration

The program under test has the following entry method:

```java
<examples.OverallJDartExample: int foo(int n, int m, long limit, double scale, boolean flag)> 
```

Hence, point the configuration to that method in `configs/sut.yml`: 

```yaml
# ============================================================
# SUT configuration
# ============================================================
# Paths should be relative to the root given in the .env file
sut:
  compiled_root: out/production/jdart-examples
  test_root: out/test/jdart-examples
  
test_generation:
  generated_tests_dir_out: data/generated-tests

target:
  class: examples.OverallJDartExample
  method: foo
  return: int
  parameters:
    - name: n
      type: int
    - name: m
      type: int
    - name: limit
      type: long
    - name: scale
      type: double
    - name: flag
      type: boolean

analysis:
  project_prefixes:
    - examples
```

When you built the project, it should have created the Java bytecode in `out/production/jdart-examples`, and for the test classes in `out/test/jdart-examples`. 

Setting the `project_prefixes` is optional and helps with reducing the analysis scope. 

## 4. Bind-mount data folder

We want to inspect the coverage graph of the `pathcov` component. Create a `development/data` folder and bind-mount it to the pathcov and covet-engine container. Add the following in `docker-compose.override.yml`. 

```yaml
services:
  pathcov:
    environment:
      - ENV=dev

    volumes:
      - ./development/data:/data

  covet-engine:
    volumes:
      - ./development/data:/data
```

## 5. Running the pipeline

> For any problems with running the pipeline, see setup in README.md

Now, just run the pipeline with executing the following in the root of this project: 
```bash
./run_pipeline.sh
```

or if it is not an executable, run: 
```bash
sh ./run_pipeline.sh
```

This will pull the `pathcov` and `covet-engine` images from Docker hub, and this can take some minutes for the first time. 

This will generate the necessary config specific to the `pathcov` preprocessing, which will create `coverage_graph.svg` inside `./development/data/visualization/icfg/coverage`. 

Open the coverage graph and notice the uncovered paths indicated in red, and notice the already covered paths indicated in yellow and green. The coverage graph is just a interprocedural control flow graph (ICFG) marked with coverage information. A block shows the (filtered) sequence of Jimple statements. Jimple is an intermediate code representation of Java bytecode to simplify program analysis and transformation.

The test suite generation should have ignored the already covered paths, and generated test cases for the uncovered execution paths. The generated test suite can be found at `jdart-examples/data/generated-tests/examples/OverallJDartExampleFooTest.java`. 

## 6. Run the generated test suite

Copy-paste `OverallJDartExampleFooTest.java` into `src/tests/examples` and run the test suite. The test suite should pass. 

You can inspect the coverage by running the pipeline again, there should be no tests generated. If you open `./development/data/visualization/icfg/coverage/coverage_graph.svg` again, all the blocks that are actual reachable are covered (green or yellow). 

