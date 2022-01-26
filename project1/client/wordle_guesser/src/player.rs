
#[allow(dead_code)]
enum Indicator {
    ABSENT = 0,
    INCORRECT = 1,
    CORRECT = 2
}

#[allow(dead_code)]
struct Guess {
    word: String,
    marks: Vec<Indicator>
}


pub struct Player {
    pub username: String,
    pub word_list: Vec<String>
}

impl Player {
    #[allow(dead_code)]
    fn make_guess(_previous_guesses: Vec<Guess>, _possible_words: Option<Vec<String>>) -> String {
        String::from("Hello World")
    }    
}
