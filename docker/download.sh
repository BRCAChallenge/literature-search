#!/usr/bin/env bash

TMPDIR=/tmp
#PDFBOX="https://repo1.maven.org/maven2/org/apache/pdfbox/pdfbox-app/2.0.5/pdfbox-app-2.0.5.jar"

#git clone https://github.com/BRCAChallenge/pubMunch-BRCA.git $TMPDIR/pubMunch
git clone https://github.com/strbean/pubMunch-BRCA.git $TMPDIR/pubMunch
#cp -R /home/joe/pubMunch-BRCA $TMPDIR/pubMunch

mkdir $TMPDIR/pubMunch/external
mirror=$(python -c "from urllib2 import urlopen; import json; print json.load( urlopen('http://www.apache.org/dyn/closer.lua?path=$path&asjson=1'))['preferred']")
wget -O $TMPDIR/pubMunch/external/pdfbox-app-2.0.11.jar ${mirror}pdfbox/2.0.11/pdfbox-app-2.0.11.jar
wget -O $TMPDIR/pubMunch/external/docx2txt-1.4.tgz https://sourceforge.net/projects/docx2txt/files/latest/download
tar -C $TMPDIR/pubMunch/external -xzf $TMPDIR/pubMunch/external/docx2txt-1.4.tgz

