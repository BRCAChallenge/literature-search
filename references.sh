echo "Downloading references..."

# Download various references from max's personal account
# REMIND Move to some more public location
wget -qO- http://hgwdev.soe.ucsc.edu/~max/pubs/tools/bigFiles.tgz \
  | tar xfzv - -C /references --strip-components 1
cp -r /pubMunch/data/* /references/

echo "Downloading hg19..."
wget -N -P /references http://hgdownload.cse.ucsc.edu/goldenPath/hg19/bigZips/hg19.2bit
wget -N -P /references http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/twoBitToFa
chmod +x /references/twoBitToFa
/references/twoBitToFa /references/hg19.2bit /references/variants/hg19.fa
rm /references/hg19.2bit

echo "Finished downloading references."
