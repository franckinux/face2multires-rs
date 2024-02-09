use std::{env, fs};
// use std::path::{Path, PathBuf};
use std::path::PathBuf;
use std::process;

// use anyhow::Result;
use clap::{Arg, ArgAction, command};
// use image::io::Reader;

use image2tiles::TileCreator;


fn main() {
    let matches = command!()
        .arg(
            Arg::new("png")
            .short('p')
            .long("png")
            .action(ArgAction::SetTrue)
            .help("Set tile image format to png instead of default jpg")
		)
        .arg(
            Arg::new("tile-size")
            .short('s')
            .long("tilesize")
            .action(ArgAction::Set)
            .default_value("512")
            .value_parser(clap::value_parser!(u16))
            .help("Set tile image size")
		)
        .arg(
            Arg::new("directory")
            .short('d')
            .long("directory")
            .default_value("output")
            .help("Set output directory of tile image files")
        )
        .arg(Arg::new("image"))
        .get_matches();

    let png_flag = *matches.get_one::<bool>("png").unwrap();
    let tile_size: u16 = *matches.get_one::<u16>("tile-size").unwrap();
    let image_path = PathBuf::from(matches.get_one::<String>("image").unwrap());

    let directory = PathBuf::from(matches.get_one::<String>("directory").unwrap());
    if !directory.exists() {
        println!("creating directory {}", directory.to_str().unwrap());
        if let Err(error) = fs::create_dir_all(directory.clone()) {
            eprintln!("directory creation error: {error}");
            process::exit(1);
        }
    }

    println!("{directory:?}");
    println!("{png_flag:?}");
    println!("{tile_size:?}");

    match TileCreator::new_from_image_path(image_path, directory, tile_size as u32, png_flag) {
        Ok(mut ic) => {
            println!("{:?}", ic.dest_path);
            println!("{}", ic.levels);
            match ic.create_tiles() {
                Ok(_) => {},
                Err(e) => {
                    eprintln!("Could not tile image:\n\t {:?}", e);
                }
            }
        },
        Err(e) => {
            eprintln!("Could not create tiler:\n\t {:?}", e);
        }
    }
}
