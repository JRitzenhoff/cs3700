
#[allow(dead_code)]
pub enum Indicator {
    ABSENT = 0,
    INCORRECT = 1,
    CORRECT = 2
}

#[allow(dead_code)]
pub struct Guess {
    pub word: String,
    pub marks: Vec<Indicator>
}


pub struct Player {
    pub username: String,
    pub word_list: Vec<String>
}

pub fn make_guess(_previous_guesses: Vec<Guess>, _word_options: Vec<String>) -> (String, Vec<String>) {
    (String::from("Hello World"), _word_options)
}