FROM ubuntu:16.04

RUN apt-get update && apt-get install -y \
  git \
  wget \
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
# ADD https://archive.apache.org/dist/pdfbox/1.6.0/pdfbox-app-1.6.0.jar /opt
RUN wget -O /opt/pdfbox-app-1.6.0.jar https://archive.apache.org/dist/pdfbox/1.6.0/pdfbox-app-1.6.0.jar
RUN wget -qO- https://sourceforge.net/projects/docx2txt/files/latest/download | tar xz -C /opt
# RUN chmod 777 /pubMunch/external/*

WORKDIR /app
ADD . /app

# pyhgvs 0.9.4
# RUN pip install git+git://github.com/counsyl/hgvs.git@aebe5bd9683f4b5937fd653ce4b13fcd4f3ebb10

# RUN pip install --upgrade pip NOTE: pyhgvs breaks with pip > v8 so don't upgrade
RUN pip install --upgrade pip
RUN pip install setuptools --upgrade
RUN pip install --no-cache-dir -r requirements.txt
