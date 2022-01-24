
use clap::Parser; // apparently required for using CLI::parse

use wordle_guesser::cmdline::CLI;
use wordle_guesser;

#[allow(dead_code)]
const DEFAULT_WORD_LIST_PATH: &str = "word_list.txt";

fn main() {
    // get the cli input
    let _cli_input = CLI::parse_from(std::env::args_os());
    
    // TODO: remove this print statement
    println!("{:?}", _cli_input);
}