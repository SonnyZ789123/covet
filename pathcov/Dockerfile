FROM maven:3.9.9-eclipse-temurin-17

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Install system dependencies
###############################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        graphviz \
        ca-certificates \
        bash && \
    rm -rf /var/lib/apt/lists/*

###############################################################################
# Project directory
###############################################################################
ENV PATHCOV_PROJECT_DIR=/pathcov-project
RUN mkdir -p ${PATHCOV_PROJECT_DIR}

###############################################################################
# Install SootUp
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
RUN git clone --branch v2.0.1 https://github.com/SonnyZ789123/SootUp.git
WORKDIR ${PATHCOV_PROJECT_DIR}/SootUp
RUN git checkout v2.0.1
RUN mvn -B clean install -DskipTests

###############################################################################
# Install intellij-coverage-model
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
RUN git clone --branch v1.0.0 https://github.com/SonnyZ789123/intellij-coverage-model.git
WORKDIR ${PATHCOV_PROJECT_DIR}/intellij-coverage-model
RUN git checkout v1.0.0
RUN mvn -B clean install -DskipTests

ENV COVERAGE_MODEL_JAR=${PATHCOV_PROJECT_DIR}/intellij-coverage-model/target/intellij-coverage-model-1.0.0.jar

###############################################################################
# Install pathcov
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
RUN git clone --branch v1.1.0 https://github.com/SonnyZ789123/pathcov.git
WORKDIR ${PATHCOV_PROJECT_DIR}/pathcov
RUN git checkout v1.1.0
RUN mvn -B clean install -DskipTests

ENV PATHCOV_JAR=${PATHCOV_PROJECT_DIR}/pathcov/target/pathcov-1.1.0.jar

###############################################################################
# Install IntelliJ Coverage Agent
###############################################################################
ENV INTELLIJ_COVERAGE_VERSION=1.0.771
ENV INTELLIJ_COVERAGE_AGENT_JAR=/opt/intellij-coverage/intellij-coverage-agent-${INTELLIJ_COVERAGE_VERSION}.jar

RUN mkdir -p /opt/intellij-coverage && \
    curl -fsSL \
      https://repo1.maven.org/maven2/org/jetbrains/intellij/deps/intellij-coverage-agent/${INTELLIJ_COVERAGE_VERSION}/intellij-coverage-agent-${INTELLIJ_COVERAGE_VERSION}.jar \
      -o ${INTELLIJ_COVERAGE_AGENT_JAR}

###############################################################################
# Install JUnit Platform Console Standalone
###############################################################################
ENV JUNIT_VERSION=1.12.2
ENV JUNIT_CONSOLE_JAR=/opt/junit/junit-platform-console-standalone-${JUNIT_VERSION}.jar

RUN mkdir -p /opt/junit && \
    curl -fsSL \
      https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/${JUNIT_VERSION}/junit-platform-console-standalone-${JUNIT_VERSION}.jar \
      -o ${JUNIT_CONSOLE_JAR}

###############################################################################
# Default
###############################################################################
WORKDIR ${PATHCOV_PROJECT_DIR}
CMD ["/bin/bash"]
