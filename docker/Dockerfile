FROM ubuntu:16.04

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y \
  python-pip \
  git \
  wget \
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
  && rm -rf /var/cache/apt/archives \
  && rm -rf /var/lib/apt/lists

# Clone brca branch of pubMunch - switch to original later
RUN git clone https://github.com/rcurrie/pubMunch.git -b brca --single-branch /pubMunch

WORKDIR /app
ADD . /app

# pyhgvs 0.9.4
# RUN pip install git+git://github.com/counsyl/hgvs.git@aebe5bd9683f4b5937fd653ce4b13fcd4f3ebb10

# RUN pip install --upgrade pip NOTE: pyhgvs breaks with pip > v8 so don't upgrade
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
