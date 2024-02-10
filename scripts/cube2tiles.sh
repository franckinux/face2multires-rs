#!/usr/bin/env bash

# requires the vips-tools package to be installed

# tile size
t=512
# output directory
d="tiles"

if [[ -d $d ]]; then
   echo "The output directory already exists"
   exit 1
fi

mkdir -p $d/fallback

# generate the tiles and fallback images
# face definition: front, back, up, down, left, right
for f in f b u d l r; do
   image2multires -d $d -s $t $1/$f.tif;
   vipsthumbnail -s 1024 -o $(readlink -f $d/fallback/$f.jpg) $1/$f.tif
done

# get image size
s=$(vipsheader -f width $1/l.tif)

# get number of levels
l=$(python3 << EOP
import math
levels = int(math.ceil(math.log(float($s) / $t, 2))) + 1
if round($s / 2**(levels - 2)) == $t:
    levels -= 1
print(levels)
EOP
)

# generate a configuration file for Pannellum panorama viewer
cat > $d/config.jon << EOF
{
   "hfov": 100,
   "autoLoad": false,
   "type": "multires",
   "multiRes": {
      "basePath": "/$d",
      "path": "/%l/%s%y_%x",
      "fallbackPath": "/fallback/%s",
      "extension": "jpg",
      "tileResolution": $t,
      "maxLevel": $l,
      "cubeResolution": $s
   }
}
EOF

exit 0
