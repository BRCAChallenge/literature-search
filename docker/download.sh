#!/usr/bin/env bash

TMPDIR=/tmp

git clone https://github.com/BRCAChallenge/pubMunch-BRCA.git $TMPDIR/pubMunch

mkdir $TMPDIR/pubMunch/external
mirror=$(python -c "from urllib2 import urlopen; import json; print json.load( urlopen('http://www.apache.org/dyn/closer.lua?path=$path&asjson=1'))['preferred']")
wget -O $TMPDIR/pubMunch/external/pdfbox-app-2.0.5.jar ${mirror}pdfbox/2.0.5/pdfbox-app-2.0.5.jar
wget -O $TMPDIR/pubMunch/external/docx2txt-1.4 https://sourceforge.net/projects/docx2txt/files/latest/download

