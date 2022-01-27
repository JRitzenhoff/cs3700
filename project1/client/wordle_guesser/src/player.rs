use std::io::{Error, ErrorKind};
use std::convert::TryFrom;

use regex::{self, Regex};


#[allow(dead_code)]
#[derive(Debug, PartialEq, Copy, Clone)]
pub enum Indicator {
    ABSENT = 0,
    INCORRECT = 1,
    CORRECT = 2
}

impl TryFrom<u8> for Indicator {
    type Error = u8;

    fn try_from(val: u8) -> Result<Self, Self::Error> {
        match val {
            v if v == Indicator::ABSENT as u8 => Ok(Indicator::ABSENT),
            v if v == Indicator::INCORRECT as u8 => Ok(Indicator::INCORRECT),
            v if v == Indicator::CORRECT as u8 => Ok(Indicator::CORRECT),
            _ => Err(val as Self::Error),
        }
    }
}

#[allow(dead_code)]
#[derive(Debug, PartialEq)]
pub struct Guess {
    pub word: String,
    pub marks: Vec<Indicator>
}


pub struct Player {
    pub username: String,
    pub word_list: Vec<String>
}

fn generate_regex(_from_guesses: Vec<Guess>) -> Result<Regex, regex::Error> {
    Regex::new("")
}


/// Returns a guess and the remaining words
pub fn make_guess(previous_guesses: Vec<Guess>, word_options: Vec<String>) -> Result<(String, Vec<String>), Error> {
    let mut remaining_words = word_options.to_vec();

    if remaining_words.len() == 0 {
        return Err(Error::new(ErrorKind::InvalidInput, String::from("Couldn't make a guess as no words remaing")))
    }

    if previous_guesses.len() == 0 {
        if let Some(new_guess) = remaining_words.pop() {
            return Ok((new_guess, remaining_words))
        }
    }

    let matcher: Regex = match generate_regex(previous_guesses) {
        Ok(re) => re,
        Err(re_err) => return Err(Error::new(ErrorKind::InvalidData, format!("Couldn't make a regex from the previous guesses {:?}", re_err)))
    };

    remaining_words.retain(|word: &String| matcher.is_match(word.as_str()));

    let guess: String = match remaining_words.pop() {
        Some(word) => word,
        None => return Err(Error::new(ErrorKind::InvalidInput, String::from("Couldn't make a guess as no words remaing after regex")))
    };

    Ok((guess, remaining_words))
}


#[cfg(test)]
mod tests {
    #[test]
    fn test_create_regex() {
        let result = 2 + 2;
        assert_eq!(result, 4);
    }
}

