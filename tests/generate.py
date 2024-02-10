#!/usr/bin/env python3

# Requires Python 3.3+, the Python Pillow and NumPy packages, and
# nona (from Hugin). The Python pyshtools package is also needed for creating
# spherical-harmonic-transform previews (which are recommended).

# generate.py - A multires tile set generator for Pannellum
# Extensions to cylindrical input and partial panoramas by David von Oheimb
# Copyright (c) 2014-2023 Matthew Petroff
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
from PIL import Image
import os
import sys
import math

# Allow large images (this could lead to a denial of service attack if you're
# running this script on user-submitted images.)
Image.MAX_IMAGE_PIXELS = None

# Handle Pillow deprecation
ANTIALIAS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS

# Parse input
parser = argparse.ArgumentParser(description='Generate a Pannellum multires tile set from a full equirectangular panorama.',
                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('inputFile', metavar='INPUT',
                    help='directory containing cube faces')
parser.add_argument('-o', '--output', dest='output', default='./output',
                    help='output directory, optionally to be used as basePath (defaults to "./output")')
parser.add_argument('-s', '--tilesize', dest='tileSize', default=512, type=int,
                    help='tile size in pixels')
parser.add_argument('-f', '--fallbacksize', dest='fallbackSize', default=1024, type=int,
                    help='fallback tile size in pixels (defaults to 1024, set to 0 to skip)')
parser.add_argument('-a', '--autoload', action='store_true',
                    help='automatically load panorama in viewer')
parser.add_argument('-q', '--quality', dest='quality', default=75, type=int,
                    help='output JPEG quality 0-100')
parser.add_argument('--png', action='store_true',
                    help='output PNG tiles instead of JPEG tiles')
parser.add_argument('-d', '--debug', action='store_true',
                    help='debug mode (print status info and keep intermediate files)')
args = parser.parse_args()

# Create output directory
if os.path.exists(args.output):
    print('Output directory "' + args.output + '" already exists')
    if not args.debug:
        sys.exit(1)
else:
    os.makedirs(args.output)

# Face order: front, back, up, down, left, right
faceLetters = ['f', 'b', 'u', 'd', 'l', 'r']

# Process input image information
print('Processing input image information...')
inputDir = args.inputFile
# check input arguments
faces = [f for f in os.listdir(inputDir) if os.path.isfile(os.path.join(args.inputFile, f))]
if len(faces) != 6:
    print('Error: the number of faces is different than 6.')
    sys.exit(1)
cubeSize = -1
for f in faces:
    f = os.path.join(args.inputFile, f)
    with Image.open(f) as image:
        w, h = image.size
        if w != h:
            print('Error: the face %s is not a square.' % f)
            sys.exit(1)
        if cubeSize == -1:
            cubeSize = w
        elif w != cubeSize:
            print("Error: all faces don't have the same size.")
            sys.exit(1)
# sort image names, it is assumed that the first letter is in "fbudlr"
faces = sorted(faces, key=lambda f: faceLetters.index(f[0]))

tileSize = min(args.tileSize, cubeSize)
levels = int(math.ceil(math.log(float(cubeSize) / tileSize, 2))) + 1
if round(cubeSize / 2**(levels - 2)) == tileSize:
    levels -= 1  # Handle edge case
extension = '.jpg'
if args.png:
    extension = '.png'

if args.debug:
    print('maxLevel: ' + str(levels))
    print('tileResolution: ' + str(tileSize))
    print('cubeResolution: ' + str(cubeSize))

# Generate tiles
print('Generating tiles...')
for f in range(0, 6):
    size = cubeSize
    faceExists = os.path.exists(os.path.join(args.inputFile, faces[f]))
    if faceExists:
        face = Image.open(os.path.join(args.inputFile, faces[f]))
        for level in range(levels, 0, -1):
            if not os.path.exists(os.path.join(args.output, str(level))):
                os.makedirs(os.path.join(args.output, str(level)))
            tiles = int(math.ceil(float(size) / tileSize))
            if (level < levels):
                face = face.resize([size, size], ANTIALIAS)
            for i in range(0, tiles):
                for j in range(0, tiles):
                    left = j * tileSize
                    upper = i * tileSize
                    right = min(j * args.tileSize + args.tileSize, size)  # min(...) not really needed
                    lower = min(i * args.tileSize + args.tileSize, size)  # min(...) not really needed
                    tile = face.crop([left, upper, right, lower])
                    if extension == ".jpg":
                        tile = tile.convert("RGB")
                    tile.save(os.path.join(args.output, str(level), faceLetters[f] + str(i) + '_' + str(j) + extension), quality=args.quality)
                    if args.debug:
                        print('level: ' + str(level) + ' tiles: ' + str(tiles) + ' tileSize: ' + str(tileSize) + ' size: ' + str(size))
                        print('left: ' + str(left) + ' upper: ' + str(upper) + ' right: ' + str(right) + ' lower: ' + str(lower))
            size = int(size / 2)

# Generate fallback tiles
if args.fallbackSize > 0:
    print('Generating fallback tiles...')
    for f in range(0, 6):
        if not os.path.exists(os.path.join(args.output, 'fallback')):
            os.makedirs(os.path.join(args.output, 'fallback'))
        if os.path.exists(os.path.join(args.inputFile, faces[f])):
            face = Image.open(os.path.join(args.inputFile, faces[f]))
            if extension == ".jpg":
                face = face.convert("RGB")
            face = face.resize([args.fallbackSize, args.fallbackSize], ANTIALIAS)
            face.save(os.path.join(args.output, 'fallback', faceLetters[f] + extension), quality = args.quality)

# Generate config file
text = []
text.append('{')
text.append('    "hfov": 100' + ',')
if args.autoload:
    text.append('    "autoLoad": true,')
text.append('    "type": "multires",')
text.append('    "multiRes": {')
text.append('        "path": "/%l/%s%y_%x",')
if args.fallbackSize > 0:
    text.append('        "fallbackPath": "/fallback/%s",')
text.append('        "extension": "' + extension[1:] + '",')
text.append('        "tileResolution": ' + str(tileSize) + ',')
text.append('        "maxLevel": ' + str(levels) + ',')
text.append('        "cubeResolution": ' + str(cubeSize))
text.append('    }')
text.append('}')
text = '\n'.join(text)
with open(os.path.join(args.output, 'config.json'), 'w') as f:
    f.write(text)
