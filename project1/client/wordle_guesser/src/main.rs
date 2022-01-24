
use clap::Parser; // apparently required for using CLI::parse

use wordle_guesser::cmdline::CLI;
use wordle_guesser::remote::launch_wordle_client;

#[allow(dead_code)]
const DEFAULT_WORD_LIST_PATH: &str = "word_list.txt";

fn main() {
    // get the cli input
    let _cli_input = CLI::parse_from(std::env::args_os());
    
    // TODO: remove this print statement
    println!("{:?}", _cli_input);

    let address = format!("{}:{}", _cli_input.hostname, _cli_input.port);

    let words: Vec<String> = vec!();

    // initialize connection
    let game_response: Result<String, String> = launch_wordle_client(address, _cli_input.encrypt, words);

    match game_response {
        Ok(secret_key) => {
            println!("{}", secret_key)
        },
        Err(err_msg) => {
            // TODO: remove this print statement
            print!("{}", err_msg)
        }
    }
}