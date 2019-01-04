FROM ubuntu:16.04

RUN apt-get update && apt-get install -y \
  git \
  wget \
  unzip \
  python-pip \
  libssl-dev \
  libffi-dev \
  libxml2-dev \
  libxmlsec1-dev \
  libsqlite3-dev \
  catdoc \
  poppler-utils \
  gnumeric \
  python-lxml \
  python-gdbm \
  openjdk-8-jdk \ 
  libpq-dev \
  ca-certificates-java \
  && rm -rf /var/cache/apt/archives \
  && rm -rf /var/lib/apt/lists

# Clone brca branch of pubMunch - switch to upstream after pull request
RUN git clone https://github.com/rcurrie/pubMunch.git -b brca --single-branch /pubMunch

# Add external tools
RUN wget -O /opt/pdfbox-app-2.0.11.jar https://archive.apache.org/dist/pdfbox/2.0.11/pdfbox-app-2.0.11.jar
RUN wget -qO- https://sourceforge.net/projects/docx2txt/files/latest/download | tar xz -C /opt

WORKDIR /app
ADD . /app

RUN pip install --upgrade pip
RUN pip install setuptools --upgrade
RUN pip install --no-cache-dir -r requirements.txt
