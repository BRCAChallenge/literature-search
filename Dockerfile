FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
  git \
  wget \
  vim \
  unzip \
  build-essential \
  pandoc \
  python-pip \
  python3-pip \
  python3-dev \
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

# Add pubMunch from fork tracking master
RUN git clone https://github.com/rcurrie/pubMunch.git -b brca --single-branch /pubMunch

# Add external tools
RUN wget -O /opt/pdfbox-app-2.0.11.jar https://archive.apache.org/dist/pdfbox/2.0.11/pdfbox-app-2.0.11.jar
RUN wget -qO- https://sourceforge.net/projects/docx2txt/files/latest/download | tar xz -C /opt

WORKDIR /app
ADD . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements-python2.txt

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements-python3.txt

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV HOME /app

ENTRYPOINT ["python3", "run.py"]
