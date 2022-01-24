
/*


*/

enum Indicator {
    ABSENT = 0
    INCORRECT = 1,
    CORRECT = 2,
}

struct Guess {
    word: String,
    marks: Vec<>
}


fn make_guess(_previous_guesses: Vec<Guess>, _possible_words: Option<Vec<String>>) -> String {
    String::from("Hello World")
}