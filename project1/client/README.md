# Rust Wordle Guesser

Plays a game of World based on the described format in https://3700.network/

### Strategy

1. Look through all of the guesses and save the letters that are correct and incorrect as well as keep track of all the characters that should be included but are in the wrong location.
2. Create a regex string that dictates which character set belongs and should be excluded at every location of the guess (for each char).
3. Run through the word list and check for words that match the regex string AND contain all of the necessary characters.
4. Just pick the first one, filter the word_list, and send that guess to the server.
5. On each guess, the word list will continue to get smaller and the regular expression should get more specific.

### Challenges

This was my second time using rust so a lot of the borrowing features of the language were not intuitive to me.
* It took me almost 3 days to allow the TcpStream to be read from and written to using the same reference

Getting the auto-grader to accept my input
* Every attempt resulted in some form of error with Cargo

### Helpful Commands

Zip the relevant contents of the assignment:
`zip -r proj1.zip wordle_guesser Makefile README.md secret_flags -x wordle_guesser/target\*`

### Local crates

Use the [Cargo Local Registry](https://lib.rs/crates/cargo-local-registry) to setup installing all of the requirements to the repository.

Save the project crates locally:
`cargo install cargo-local-registry`
`cargo local-registry --sync <path/to/Cargo.lock> <path/to/registry>`
`cargo local-registry --sync Cargo.lock registry`