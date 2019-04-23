echo "Downloading references..."

# Download various references from max's personal account
# REMIND Move to some more public location
wget -qO- http://hgwdev.soe.ucsc.edu/~max/pubs/tools/bigFiles.tgz \
  | tar xfzv - -C /references --strip-components 1
cp -r /pubMunch/data/* /references/

echo "Finished downloading references."
