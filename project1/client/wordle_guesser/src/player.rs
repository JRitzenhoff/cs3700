use std::io::{Error, ErrorKind};
use std::collections::HashSet;
use std::convert::TryFrom;


use regex::{self, Regex};

const DEFAULT_CHAR_RANGE: &str = "a-z";



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


#[derive(Debug, PartialEq)]
pub struct Guess {
    pub word: String,
    pub marks: Vec<Indicator>
}


pub struct Player {
    pub username: String,
    pub word_list: Vec<String>
}


fn generate_char_options(collection: &HashSet<char>) -> String {
    if collection.is_empty() { 
        return String::from(DEFAULT_CHAR_RANGE)
    } 
    else {
        return collection.iter().collect::<String>() 
    };
}

/// Iterate through each guess:
/// 1. If a letter is Indicator::CORRECT
///     - override any previous setting with the current letter
/// 2. If a letter is Indicator::ABSENT
///     - add to "not these letters list"
/// 3. If a letter is Indicator::INCORRECT
///     - add to "not this letter list"
/// - add to word has one of
fn generate_regex(from_guesses: Vec<Guess>) -> Result<(Regex, HashSet<char>), regex::Error> {
    let mut correct_letters: Vec<Option<char>> = Vec::new();
    let mut wrong_letters: Vec<HashSet<char>> = Vec::new();

    let mut misplaced_letters: HashSet<char> = HashSet::new();

    for guess in from_guesses.into_iter() {
        for (index, (letter, ind)) in guess.word.chars().zip(guess.marks).enumerate() {
            // first pass
            if correct_letters.len() <= index {
                correct_letters.push(None);
                wrong_letters.push(HashSet::new());
            }

            // if there is a correct letter, make sure that dominates
            if correct_letters[index].is_some() {
                wrong_letters[index].clear();
                continue;
            }

            match ind {
                Indicator::CORRECT => {
                    correct_letters[index] = Some(letter);
                    wrong_letters[index].clear();
                },
                Indicator::ABSENT => {
                    wrong_letters[index].insert(letter);
                },
                Indicator::INCORRECT => {
                    misplaced_letters.insert(letter);
                }
            }
        }
    }

    let mut binary_string: String = String::new();

    for (optional_correct, definite_wrongs) in correct_letters.iter().zip(wrong_letters.iter()) {
        if let Some(letter) = optional_correct {
            binary_string.push(*letter);
            continue;
        }

        if definite_wrongs.is_empty() {
            binary_string.push_str(DEFAULT_CHAR_RANGE);
        } 
        else {
            let wrong_chars: String = collection.iter().collect::<String>();
            let wrong_regex: String = format!("[^{}]", wrong_chars);
            binary_string.push_str(wrong_regex.as_str()); 
        };
    }

    // println!("Correct: {:?}", correct_letters);
    // println!("Incorrect: {:?}", wrong_letters);
    // println!("Possible: {:?}", misplaced_letters);

    /*
        [xyz]         A character class matching either x, y or z (union).
        [^xyz]        A character class matching any character except x, y and z.
        [a-z]         A character class matching any character in range a-z.
        [[:alpha:]]   ASCII character class ([A-Za-z])
    */

    let binary_match: Regex = Regex::new(binary_string.as_str())?;
    Ok((binary_match, misplaced_letters))
}


/// Returns a guess and the remaining words
pub fn make_guess(previous_guesses: Vec<Guess>, word_options: Vec<String>) -> Result<(String, Vec<String>), Error> {
    let mut remaining_words = word_options.to_vec();

    if previous_guesses.len() == 0 {
        if let Some(new_guess) = remaining_words.pop() {
            return Ok((new_guess, remaining_words))
        }
        else {
            return Err(Error::new(ErrorKind::InvalidInput, String::from("Couldn't make a guess as no words remaing")))
        }
    }

    let (binary_matcher, must_contain): (Regex, HashSet<char>) = match generate_regex(previous_guesses) {
        Ok(regs) => regs,
        Err(re_err) => return Err(Error::new(ErrorKind::InvalidData, format!("Couldn't make a regex from the previous guesses {:?}", re_err)))
    };

    remaining_words.retain(|word: &String| binary_matcher.is_match(word.as_str()) && 
                                           must_contain.iter().all(|c: &char| word.contains(*c)));

    let guess: String = match remaining_words.pop() {
        Some(word) => word,
        None => return Err(Error::new(ErrorKind::InvalidInput, String::from("Couldn't make a guess as no words remaing")))
    };

    Ok((guess, remaining_words))
}



#[cfg(test)]
mod tests {
    #[allow(unused_imports)]
    use regex::Regex;

    use super::{
        Guess, 
        Indicator as IND,
        generate_regex, make_guess
    };

    #[test]
    fn test_create_regex() {
        // cargo test test_create_regex -- --nocapture

        // THE WORD IS: hello
        let guesses = vec![
            Guess { word: String::from("hills"), marks: vec![IND::CORRECT, IND::ABSENT, IND::CORRECT, IND::CORRECT, IND::ABSENT]},
            Guess { word: String::from("hallt"), marks: vec![IND::CORRECT, IND::ABSENT, IND::CORRECT, IND::CORRECT, IND::ABSENT]}
        ];

        let (binary, contain) = generate_regex(guesses).unwrap();
        println!("{} + {:?}", binary, contain);
    }

    #[test]
    fn test_make_guess() {
        // cargo test test_make_guess -- --nocapture

        // THE WORD IS: hello
        let guesses = vec![
            Guess { word: String::from("hills"), marks: vec![IND::CORRECT, IND::ABSENT, IND::CORRECT, IND::CORRECT, IND::ABSENT]},
            Guess { word: String::from("hallt"), marks: vec![IND::CORRECT, IND::ABSENT, IND::CORRECT, IND::CORRECT, IND::ABSENT]}
        ];

        let words = vec![
            String::from("hallo"),
            String::from("nothi"),
            String::from("adllk"),
            String::from("halls"),
            String::from("helll"),
            String::from("hello")
        ];

        let (guess, remaining_words): (String, Vec<String>) = make_guess(guesses, words).unwrap();

        assert_eq!(remaining_words, vec!["helll"]);
        assert_eq!(guess, String::from("hello"));

    }

}

