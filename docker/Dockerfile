FROM ubuntu:16.04

MAINTAINER Audrey Musselman-Brown, almussel@ucsc.edu

RUN apt-get update && apt-get install -y git python-gdbm python-pip xvfb firefox wget poppler-utils default-jre catdoc
RUN pip install numpy mock
RUN pip install biopython pygr requests selenium==3.3.0 pyvirtualdisplay html2text synapseclient
RUN pip install ga4gh==0.3.5 || true

RUN git clone https://github.com/counsyl/hgvs.git
# taking pyhgvs 0.9.4
RUN cd hgvs && git checkout aebe5bd9683f4b5937fd653ce4b13fcd4f3ebb10 && python setup.py install

ADD wrapper.sh /opt/wrapper.sh
ADD download.sh /opt/download.sh
ADD download_data.sh /opt/download_data.sh
ADD correlate.py /opt/correlate.py
ADD getpubs.py /opt/getpubs.py
ADD brca_tests /opt/brca_tests
ADD test_pipeline.py /opt/test_pipeline.py
ADD test_correlate.py /opt/test_correlate.py
ADD test_crawl.py /opt/test_crawl.py
ADD test_findmutations.py /opt/test_findmutations.py

# prevent keyring from prompting for password
# maybe this should be $HOME/.local...
ADD keyringrc.cfg /root/.local/share/python_keyring/keyringrc.cfg
RUN chmod +x /opt/*

RUN mkdir /opt/bin
ENV PATH $PATH:/opt/bin
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.15.0/geckodriver-v0.15.0-linux64.tar.gz
RUN tar xzf geckodriver-v0.15.0-linux64.tar.gz  -C /opt/bin && rm geckodriver-v0.15.0-linux64.tar.gz

# set entrypoint
ENTRYPOINT ["/opt/wrapper.sh"]

