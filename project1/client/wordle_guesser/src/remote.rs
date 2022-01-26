
// use std::io::prelude::*;
use std::io::{Error, Read, Write, BufReader, BufRead};
use std::net::TcpStream;
use std::collections::HashMap;

use native_tls::{TlsConnector, TlsStream};
use json::{JsonValue};

use crate::player::{Player};


// ----------------------------------------------------------------
// CONSTANTS
const TYPE_KEY: &str = "type";
const USERNAME_KEY: &str = "northeastern_username";
// const ID_KEY: &str = "id";
// const WORD_KEY: &str = "word";
// const PAST_GUESSES_KEY: &str = "guesses";
// const FLAG_KEY: &str = "flag";

const HELLO_MSG_KEY: &str = "hello";
// const RETRY_MSG_KEY: &str = "retry";
// const START_MSG_KEY: &str = "start";
// const GUESS_MSG_KEY: &str = "guess";
// const BYE_MSG_KEY: &str = "bye";
// ----------------------------------------------------------------


/// Accepts a list of arguments
fn prepare_message(message_components: HashMap<&str, &str>) -> Vec<u8> {
    let mut json_object = JsonValue::new_object();

    for (key, value) in message_components.into_iter() {
        json_object[key] = value.into();
    }

    let mut object_string: String = json_object.dump();
    object_string.push('\n');

    object_string.as_bytes().to_owned()
}

pub fn play_game<T>(client_stream: T, player: Player) -> Result<String, Error> where T: Read+Write {
    // Little hack to get a BufReader and a Stream writer 
    let mut client_reader = BufReader::new(client_stream);
    let client_writer: &mut T = client_reader.get_mut();

    // don't care about anything other than that the stream implements read and write
    let hello_msg: Vec<u8> = prepare_message(HashMap::from([(TYPE_KEY, HELLO_MSG_KEY), 
                                                            (USERNAME_KEY, player.username.as_str())]));
    client_writer.write_all(&hello_msg)?;



    let mut hello_response: String = String::new();
    client_reader.read_line(&mut hello_response)?;
    // let hello_response: String = String::from_utf8(response.to_vec()).unwrap();

    Ok(format!("Response: {}", hello_response))
}


/// Play a game of Wordle
pub fn run_wordle_client(hostname: String, port: u16, encrypt_messages: bool, player: Player) -> Result<String, Error> {
    
    let address = format!("{}:{}", hostname, port);
    let stream: TcpStream = TcpStream::connect(address)?;

    if !encrypt_messages {
        return play_game(stream, player);
    }

    let tls_connector: TlsConnector = TlsConnector::new().unwrap();

    let static_hostname: &str = hostname.as_str();
    let tls_stream: TlsStream<TcpStream> = tls_connector.connect(static_hostname, stream).unwrap();

    play_game(tls_stream, player)
}