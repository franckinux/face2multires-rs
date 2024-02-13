This programs converts a single image to tiles in multires format.

This work has been inspired by the Pannellum
(https://github.com/mpetroff/pannellum) and dzi (https://github.com/n-k/dzi)
projects.

It is usualy used to convert a cube face to tiles. In this case, the image is a
square but this tool is generalized so that it can work on rectangle shaped
images.

I made the choice of a tool that makes a unique operation. So it does not
operate on the 6 faces nor it does not generate a configuration file for any
panarama viewer. For these purposes, you can use a script of your own. An
example shell script `cube2tiles.sh` is provided in the scripts directory.

I didn't find any specification of the multires tile format. You can find the
Python script `generate.py` in the test directory. It comes from the Pannellum
project. This a modified version of the original script: the convertion from
equirectangular to cube faces has been removed.

# Usage

```
Generate multires tiles from an image

Usage: image2multires [OPTIONS] [image]

Arguments:
  [image]

Options:
  -p, --png                    Set tile image format to png instead of default jpg
  -s, --tilesize <tile-size>   Set tile image size [default: 512]
  -d, --directory <directory>  Set output directory of tile image files [default: output]
  -h, --help                   Print help
  -V, --version                Print version
```

# General context or workflow

My workflow for generating a parorama is:

1. Stitch the images to produce an equirectangular image;
2. Convert the equirectangular image to 6 cube faces;
3. Do some changes on the down image to have a nadir without foreign objects,
   artifacts or hole;
4. Generate tiles from the cube faces. This is where this program operates;
5. Delete the original equirectangular image.

# Known issues

The following error may happen:

```
Unsupported source image: invalid code in LZW stream
```

This is caused by the underlying libraries. The only workaroud I can suggest is
to open the image and save it.

See issue https://github.com/image-rs/image-tiff/issues/191.
