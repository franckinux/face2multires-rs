use std::fs::File;
use std::io::{BufReader, Write};
use std::path::PathBuf;

use image::{
    DynamicImage,
    GenericImageView,
    ImageError,
    imageops::{crop_imm, FilterType, resize},
    io::Reader
};


#[derive(thiserror::Error, Debug)]
pub enum TilingError {
    #[error("Unsupported source image: {0}")]
    UnsupportedSourceImage(String),
    #[error("Unexpected error")]
    UnexpectedError,
    #[error("Unsupported source image: {0}")]
    ImageError(#[from] ImageError),
    #[error("IO error: {0}")]
    IOError(#[from] std::io::Error),
}

pub type DZIResult<T, E = TilingError> = Result<T, E>;

/// A tile creator, this struct and associated functions
/// implement the DZI tiler
#[derive(Debug)]
pub struct TileCreator {
    /// path of destination directory where tiles will be stored
    pub dest_path: PathBuf,
    /// source image
    pub image: DynamicImage,
    /// size of individual tiles in pixels
    pub tile_size: u32,
    /// size of cube in pixels
    pub cube_size: u32,
    /// total number of levels of tiles
    pub levels: u32,
}


impl TileCreator {
    pub fn new_from_image_path(
        image_path: PathBuf, dest_path: PathBuf, tile_size: u32, png: bool
    ) -> DZIResult<Self> {
        let file = File::open(image_path)?;
        let reader = BufReader::new(file);
        let mut img_reader = Reader::new(reader).with_guessed_format()?;
        img_reader.no_limits();
        let im = img_reader.decode()?;
        let (h, w) = im.dimensions();
        if h != w {
            return Err(TilingError::UnsupportedSourceImage("This not a square image".into()));
        }

        let cube_size = h;
        let tile_size = tile_size.min(h);
        let mut levels: u32 = (cube_size as f64 / tile_size as f64).log2().ceil() as u32 + 1;
        if (cube_size as f64 / 2u32.pow(levels - 2) as f64).round() as u32 == tile_size {
            levels -= 1  // Handle edge case
        }

        Ok(Self {
            dest_path,
            image: im,
            tile_size,
            cube_size,
            levels,
        })
    }

    /// Create DZI tiles
    pub fn create_tiles(&mut self) -> DZIResult<()> {
        let mut size = self.cube_size;
        for level in (1..=self.levels).rev() {
            // let p = self.dest_path.join(format!("{}", level));
            let p = self.dest_path.join(level.to_string());
            std::fs::create_dir_all(&p)?;

            let tiles = (size as f64 / self.tile_size as f64).ceil() as u32;
            if level < self.levels {
                self.image = image::DynamicImage::ImageRgba8(
                    resize(&self.image, size, size, FilterType::Triangle)
                );
            }
            for i in 0..tiles {
                for j in 0..tiles {
                    let left = j * self.tile_size;
                    let upper = i * self.tile_size;
                    let width = if left + self.tile_size >= self.cube_size {
                        self.cube_size - left
                    } else {
                        self.tile_size
                    };
                    let height = if upper + self.tile_size >= self.cube_size {
                        self.cube_size - upper
                    } else {
                        self.tile_size
                    };
                    let tile_image = self.image.crop_imm(left, upper, width, height);

                    let tile_path = self.dest_path.join(level.to_string()).join(format!("x{}_{}.png", i, j));
                    // println!("{tile_path:?}, {width}, {height}");
                    tile_image.save(tile_path)?;
                }
            }

            size = size / 2;
            // println!("{size}");
        }
        Ok(())
    }

    // for i in range(0, tiles):
    //     for j in range(0, tiles):
    //         left = j * tileSize
    //         upper = i * tileSize
    //         right = min(j * args.tileSize + args.tileSize, size)   # min(...) not really needed
    //         lower = min(i * args.tileSize + args.tileSize, size)   # min(...) not really needed
    //         tile = face.crop([left, upper, right, lower])
    //         if extension == ".jpg":
    //             tile = tile.convert("RGB")
    //         tile.save(os.path.join(args.output, str(level), faceLetters[f] + str(i) + '_' + str(j) + extension), quality=args.quality)
    //         if args.debug:
    //             print('level: ' + str(level) + ' tiles: ' + str(tiles) + ' tileSize: ' + str(tileSize) + ' size: ' + str(size))
    //             print('left: ' + str(left) + ' upper: ' + str(upper) + ' right: ' + str(right) + ' lower: ' + str(lower))
    // size = int(size / 2)
}


// #[cfg(test)]
// mod tests {
//     use std::path::PathBuf;
//
//     use crate::TileCreator;
//
//     #[test]
//     fn test_info() {
//         let path = PathBuf::from(format!("{}/test_data/test.jpg", env!("CARGO_MANIFEST_DIR")));
//         let ic = TileCreator::new_from_image_path(path.as_path(), 254);
//         assert!(ic.is_ok());
//         let ic = ic.unwrap();
//         assert_eq!(ic.levels, 14);
//         let (w, h) = ic.get_dimensions(ic.levels - 1).unwrap();
//         assert_eq!(w, 5184);
//         assert_eq!(h, 3456);
//
//         let (w, h) = ic.get_dimensions(1).unwrap();
//         assert_eq!(w, 2);
//         assert_eq!(h, 1);
//
//         let (c, r) = ic.get_tile_count(13).unwrap();
//         assert_eq!(c, 21);
//         assert_eq!(r, 14);
//     }
// }
