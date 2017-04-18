FROM ubuntu

MAINTAINER Audrey Musselman-Brown, almussel@ucsc.edu

RUN apt-get update && apt-get install -y git python-gdbm python-pip xvfb firefox wget poppler-utils default-jre
RUN pip install numpy
RUN pip install biopython pygr requests selenium==3.3.0 pyvirtualdisplay html2text==2016.9.19 synapseclient
RUN pip install ga4gh==0.3.5 || true

ADD wrapper.sh /opt/wrapper.sh
ADD download.sh /opt/download.sh
ADD pubs_json.py /opt/pubs_json.py
ADD getpubs.py /opt/getpubs.py
RUN chmod +x /opt/*

RUN mkdir /opt/bin
ENV PATH $PATH:/opt/bin
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.15.0/geckodriver-v0.15.0-linux64.tar.gz
RUN tar xzf geckodriver-v0.15.0-linux64.tar.gz  -C /opt/bin && rm geckodriver-v0.15.0-linux64.tar.gz

# set entrypoint
ENTRYPOINT ["/opt/wrapper.sh"]

