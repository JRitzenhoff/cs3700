use std::fs::File;
use std::io::{BufReader, Error};
use std::io::prelude::*;

use std::path::PathBuf;

pub mod cmdline;
pub mod remote;
pub mod player;


/// Extract all of the String words from a provided file
pub fn read_word_contents(word_list: PathBuf) -> Result<Vec<String>, Error> {
    let file_object: File = File::open(word_list)?; // '?' returns the appropriate Error if unwrapping does not work
    let reader = BufReader::new(file_object);

    let words: Vec<String> = reader.lines()
                                    .map(|l| l.unwrap())
                                    .collect();
    Ok(words)
}


#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        let result = 2 + 2;
        assert_eq!(result, 4);
    }
}
