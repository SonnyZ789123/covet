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

FROM ubuntu:14.04

LABEL maintainer="yoranmertens0@gmail.com"

###############################################################################
# Base system & Java 8
###############################################################################
RUN apt-get update -y && \
    apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository ppa:openjdk-r/ppa -y && \
    apt-get update -y && \
    apt-get install -y \
        openjdk-8-jdk \
        ant \
        maven \
        git \
        junit \
        build-essential \
        python \
        antlr3 \
        wget && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java && \
    update-alternatives --set javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV JUNIT_HOME=/usr/share/java

###############################################################################
# Project directory
###############################################################################
RUN mkdir /covet-engine-project
ENV COVET_DIR=/covet-engine-project

WORKDIR ${COVET_DIR}

###############################################################################
# Install jpf-core
###############################################################################
RUN git clone https://github.com/javapathfinder/jpf-core.git
WORKDIR ${COVET_DIR}/jpf-core
RUN git checkout JPF-8.0 && ant

###############################################################################
# Install jConstraints
###############################################################################
WORKDIR ${COVET_DIR}
RUN git clone https://github.com/samsbp/jconstraints.git
WORKDIR ${COVET_DIR}/jconstraints
RUN mvn install

###############################################################################
# Install Z3 4.4.1 (Linux binary)
###############################################################################
WORKDIR ${COVET_DIR}
RUN wget https://github.com/Z3Prover/z3/releases/download/z3-4.4.1/z3-4.4.1-x64-ubuntu-14.04.zip && \
    unzip z3-4.4.1-x64-ubuntu-14.04.zip && \
    rm z3-4.4.1-x64-ubuntu-14.04.zip && \
    ln -s z3-4.4.1-x64-ubuntu-14.04 z3

WORKDIR ${COVET_DIR}/z3/bin
RUN mvn install:install-file \
    -Dfile=com.microsoft.z3.jar \
    -DgroupId=com.microsoft \
    -DartifactId=z3 \
    -Dversion=4.4.1 \
    -Dpackaging=jar

ENV LD_LIBRARY_PATH=${COVET_DIR}/z3/bin

###############################################################################
# Install jconstraints-z3
###############################################################################
WORKDIR ${COVET_DIR}
RUN git clone https://github.com/samsbp/jconstraints-z3.git
WORKDIR ${COVET_DIR}/jconstraints-z3
RUN mvn install

###############################################################################
# Configure JPF
###############################################################################
RUN mkdir -p /root/.jpf && \
    echo "jpf-core = ${COVET_DIR}/jpf-core"            >> /root/.jpf/site.properties && \
    echo "jpf-jdart = ${COVET_DIR}/covet-engine"       >> /root/.jpf/site.properties && \
    echo "extensions=\${jpf-core},\${jpf-jdart}"       >> /root/.jpf/site.properties

###############################################################################
# Configure jConstraints extensions
###############################################################################
RUN mkdir -p /root/.jconstraints/extensions && \
    cp ${COVET_DIR}/jconstraints-z3/target/jconstraints-z3-0.9.1-SNAPSHOT.jar /root/.jconstraints/extensions && \
    cp /root/.m2/repository/com/microsoft/z3/4.4.1/z3-4.4.1.jar \
         /root/.jconstraints/extensions/com.microsoft.z3.jar

###############################################################################
# Install covet-engine (forked JDart)
###############################################################################
WORKDIR ${COVET_DIR}
ENV COVET_VERSION=4.4.0
RUN git clone --branch v${COVET_VERSION} https://github.com/SonnyZ789123/covet-engine.git
WORKDIR ${COVET_DIR}/covet-engine
RUN git checkout v${COVET_VERSION}
RUN ant

WORKDIR ${COVET_DIR}

###############################################################################
# Default command (drop into shell)
###############################################################################
CMD ["/bin/bash"]
