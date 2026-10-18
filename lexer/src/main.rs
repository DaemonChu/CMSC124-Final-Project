use std::error::Error;
use std::fs::File;
use std::io::prelude::*;
use std::path::Path;
use regex::Regex;

fn main(){

    // read input files
    // sample .lol files can be found at /example
    let path = Path::new("example/sample.lol");
    let display = path.display();

    let mut file = match File::open(&path) {
        Err(why) => panic!("couldn't open {}: {}", display, why),
        Ok(file) => file,
    };

    let mut contents = String::new();

    match file.read_to_string(&mut contents) {
        Err(why) => panic!("couldn't read {}: {}", display, why),
        Ok(_) => { println!("{} contains:\n{}", display, contents);}
    }  

    //ident applies to var, func, and loop identifiers
    let ident = Regex::new(r"^[a-zA-Z][a-zA-Z0-9_]*$").unwrap();

    //literals
    let numbr_lit = Regex::new(r"^-?[0-9]+$").unwrap();
    let numbar_lit = Regex::new(r"^-?[0-9]+\.[0-9]+$").unwrap();
    let yarn_lit = Regex::new(r#""[^"]*""#).unwrap();
    let troof_lit = Regex::new(r"^(WIN|FAIL)$").unwrap();
    let type_lit = Regex::new(r"^(NOOB|NUMBR|NUMBAR|YARN|TROOF)$").unwrap();

    // proces contents of the file 
    for line in contents.lines() {
        for element in line.split_whitespace() {
            
            //keywords(direct comparison kagaya sa ics os codes na maraming if-else statements)
            if element == "HAI" {
                println!("{} : Code Delimiter", element);
            } else if element == "KTHXBYE" {
                println!("{} : Code Delimiter", element);
            } else if element == "WAZZUP" {
                println!("{} : Variable Declaration Delimiter", element);
            } else if element == "BUHBYE" {
                println!("{} : Variable Declaration Delimiter", element);
            } else if element == "BTW" {
                println!("{} : Comment", element);
            } //etc.....
        }
    }
}

