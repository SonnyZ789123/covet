# Copyright (c) 2025-2026 Yoran Mertens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

FROM eclipse-temurin:17-jdk

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Install runtime system dependencies only
###############################################################################
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        graphviz \
        curl && \
    rm -rf /var/lib/apt/lists/*

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
# Install pathcov
###############################################################################
ENV PATHCOV_VERSION=2.7.0
ENV PATHCOV_JAR=/opt/pathcov/pathcov-${PATHCOV_VERSION}.jar

RUN mkdir -p /opt/pathcov && \
    curl -fsSL \
      https://github.com/SonnyZ789123/pathcov/releases/download/v${PATHCOV_VERSION}/pathcov-${PATHCOV_VERSION}.jar \
      -o ${PATHCOV_JAR}

###############################################################################
# Default
###############################################################################
CMD ["/bin/bash"]
