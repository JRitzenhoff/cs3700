
// use std::io::prelude::*;
use std::collections::HashMap;
use std::convert::TryFrom;
use std::io::{Read, Write, BufReader, BufRead, Error, ErrorKind};
use std::net::TcpStream;

use native_tls::{TlsConnector, TlsStream};
use json::{JsonValue};

use crate::player::{self, Player, Guess, Indicator};


// ----------------------------------------------------------------
// CONSTANTS
const TYPE_KEY: &str = "type";
const USERNAME_KEY: &str = "northeastern_username";
const ID_KEY: &str = "id";
const WORD_KEY: &str = "word";
const PAST_GUESSES_KEY: &str = "guesses";
const FLAG_KEY: &str = "flag";
const MESSAGE_KEY: &str = "message";
const SCORE_KEY: &str = "marks";

const HELLO_MSG_KEY: &str = "hello";
const GUESS_MSG_KEY: &str = "guess";
const START_MSG_KEY: &str = "start";
const RETRY_MSG_KEY: &str = "retry";
const BYE_MSG_KEY: &str = "bye";
const ERROR_MSG_KEY: &str = "error";
// ----------------------------------------------------------------

#[derive(Debug, PartialEq)]
enum ResponseType {
    START,
    RETRY,
    BYE,
    ERROR,
    UNKNOWN(String)
}

impl From<&str> for ResponseType {
    fn from(input: &str) -> Self {
        match input {
            START_MSG_KEY => ResponseType::START,
            RETRY_MSG_KEY => ResponseType::RETRY,
            BYE_MSG_KEY => ResponseType::BYE,
            ERROR_MSG_KEY => ResponseType::ERROR,
            _ => ResponseType::UNKNOWN(String::from(input))
        }
    }
}

#[derive(Debug, PartialEq)]
enum ContentType {
    MATCHES(Vec<Guess>),
    FLAG(String)
}

/// Accepts a list of arguments
fn prepare_message(message_components: HashMap<&str, &str>) -> Vec<u8> {
    let mut json_message = JsonValue::new_object();

    for (key, value) in message_components.into_iter() {
        json_message[key] = value.into();
    }

    let mut object_string: String = json_message.dump();
    object_string.push('\n');

    object_string.as_bytes().to_owned()
}

fn extract_json_field(json_object: &JsonValue, expected_key: &str) -> Result<JsonValue, Error> {
    let key_value = json_object[expected_key].to_owned();

    if key_value.is_null() { 
        Err(Error::new(ErrorKind::InvalidData, format!("JSON {} key missing in {}", expected_key, json_object)))
    }
    else {
        Ok(key_value)
    }
}

fn parse_response(json_response: &JsonValue) -> Result<(ResponseType, String), Error> {
    let type_value = extract_json_field(json_response, TYPE_KEY)?;
    let response_type: ResponseType = ResponseType::from(type_value.to_string().as_str());

    match response_type {
        ResponseType::ERROR => {
            // an error doesn't have an ID field
            let err_msg = json_response[MESSAGE_KEY].to_owned();
            return Err(Error::new(ErrorKind::Unsupported, format!("Wordle returned error message {}", err_msg.to_string())))
        },
        ResponseType::UNKNOWN(msg) => return Err(Error::new(ErrorKind::InvalidData, format!("JSON unknown response type {}", msg))),
        _ => {}
    }

    let id_value = extract_json_field(&json_response, ID_KEY)?.to_string();
    return Ok((response_type, id_value))
}


fn parse_hello_response(raw_response: String) -> Result<String, Error> {
    let json_response = json::parse(raw_response.as_str()).unwrap();
    let (resp_type, id_value) = parse_response(&json_response)?;

    match resp_type {
        ResponseType::START => Ok(id_value),
        _ => Err(Error::new(ErrorKind::InvalidData, format!("Expected response type {:?} and received {:?}", ResponseType::START, resp_type)))
    }
}

fn parse_marks(json_marks: JsonValue) -> Result<Vec<Indicator>, Error> {
    if !json_marks.is_array() {
        return Err(Error::new(ErrorKind::InvalidData, format!("Expected array of marks objects and received {:?}", json_marks)))
    }

    let mut marks: Vec<Indicator> = Vec::new();

    for json_indicator in json_marks.members() {

        let indicator: Indicator = match Indicator::try_from(json_indicator.as_u8().unwrap()) {
            Ok(enum_val) => enum_val,
            Err(raw_val) => return Err(Error::new(ErrorKind::InvalidData, format!("Unknown indicator value {}", raw_val)))
        };

        marks.push(indicator);
    }

    Ok(marks)
}

fn parse_guess(json_guess: JsonValue) -> Result<Guess, Error> {
    let guessed_word: String = extract_json_field(&json_guess, WORD_KEY)?.to_string();
    let guessed_raw_marks: JsonValue = extract_json_field(&json_guess, SCORE_KEY)?;

    let guessed_marks = parse_marks(guessed_raw_marks)?;

    Ok(Guess { word: guessed_word, marks: guessed_marks })
}

fn parse_guesses(json_guesses: JsonValue) -> Result<Vec<Guess>, Error> {
    if !json_guesses.is_array() {
        return Err(Error::new(ErrorKind::InvalidData, format!("Expected array of guess objects and received {:?}", json_guesses)))
    }

    let mut guesses: Vec<Guess> = Vec::new();
    
    for json_guess in json_guesses.members() {
        let past_guess: Guess = parse_guess(json_guess.to_owned())?;
        guesses.push(past_guess);
    }
    
    Ok(guesses)
}


fn parse_guess_response(raw_response: String, player_id: &str) -> Result<ContentType, Error> {
    let json_response = json::parse(raw_response.as_str()).unwrap();
    let (resp_type, id_value) = parse_response(&json_response)?;

    if id_value != player_id {
        return Err(Error::new(ErrorKind::InvalidData, format!("Received ID {} instead of expected {}", id_value, player_id)))
    }

    match resp_type {
        ResponseType::RETRY => {
            let json_guesses = extract_json_field(&json_response, PAST_GUESSES_KEY)?;
            let previous_guesses = parse_guesses(json_guesses)?;
            Ok(ContentType::MATCHES(previous_guesses))
        },
        ResponseType::BYE => {
            let content = extract_json_field(&json_response, FLAG_KEY)?;
            Ok(ContentType::FLAG(content.to_string()))
        },
        _ => Err(Error::new(ErrorKind::InvalidData, format!("Expected response type {:?} and received {:?}", ResponseType::RETRY, resp_type)))
    }
}

pub fn play_game<Stream>(mut client_stream: Stream, player: Player) -> Result<String, Error> where Stream: Read+Write {
    // don't care about anything other than that the stream implements read and write
    let hello_msg: Vec<u8> = prepare_message(HashMap::from([(TYPE_KEY, HELLO_MSG_KEY), 
                                                            (USERNAME_KEY, player.username.as_str())]));
    client_stream.write_all(&hello_msg)?;

    // read the response from the server
    let mut hello_response: String = String::new();
    {
        let mut client_reader = BufReader::new(&mut client_stream);
        client_reader.read_line(&mut hello_response)?;
    }

    let player_id_string: String = parse_hello_response(hello_response)?;
    let player_id = player_id_string.as_str();

    let mut previous_guesses: Vec<Guess> = Vec::new();
    let mut word_options: Vec<String> = player.word_list;

    // make guesses
    let secret_key: String = loop {
        let (guess, remaining_words) = player::make_guess(previous_guesses, word_options.to_vec()).unwrap();
        word_options = remaining_words;

        let guess_msg: Vec<u8> = prepare_message(HashMap::from([(TYPE_KEY, GUESS_MSG_KEY),
                                                                (ID_KEY, player_id),
                                                                (WORD_KEY, guess.as_str())]));
        
        client_stream.write_all(&guess_msg)?;
        let mut guess_response: String = String::new();
        {
            let mut client_reader = BufReader::new(&mut client_stream);
            client_reader.read_line(&mut guess_response)?;
        }

        match parse_guess_response(guess_response, player_id)? {
            ContentType::MATCHES(past_guesses) => {
                previous_guesses = past_guesses;
            },
            ContentType::FLAG(key) => {
                break key;
            }
        }
    };

    Ok(format!("Response: {}", secret_key))
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