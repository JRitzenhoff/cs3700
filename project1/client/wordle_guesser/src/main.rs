use std::io::Error;

use clap::Parser; // apparently required for using CLI::parse

use wordle_guesser::{self, remote, cmdline::CLI, player::Player};

fn main() -> Result<(), Error> {
    
    // get the cli input
    let cli_input = CLI::parse_from(std::env::args_os());

    let word_options: Vec<String> = wordle_guesser::read_word_contents(cli_input.word_list)?;
    let wordle_player: Player = Player { username: cli_input.username, word_list: word_options };

    // play a game of wordle
    let secret_key: String = remote::run_wordle_client(cli_input.hostname, cli_input.port, cli_input.encrypt, wordle_player)?;
    println!("{}", secret_key);

    Ok(())
}