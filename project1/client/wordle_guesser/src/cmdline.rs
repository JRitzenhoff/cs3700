use std::path::PathBuf;

use clap::Parser;

// ----------------------------------------------------------------
// CONSTANTS
// const DEFAULT_HOSTNAME: &str = "proj1.3700.network";
const DEFAULT_PORT: &str = "27993";
const DEFAULT_TLS_PORT: &str = "27994";
const DEFAULT_WORD_LIST_PATH: &str = "wordle_guesser/word_list.txt";
// ----------------------------------------------------------------


#[derive(Debug, Parser)]
#[clap(about="Program that connects to a Khoury server and plays a game of Wordle")]
pub struct CLI {
    #[clap(short='s', long="encrypt", required(false), help="Use to use a TLS encrypted socket")]
    #[clap(parse(from_flag))]
    pub encrypt: bool,

    /// If port is not defined:
    /// 
    /// * AND the encryption flag is NOT present
    ///     * use DEFAULT_PORT
    /// 
    /// * AND the TLS encryption flag IS present without any trailing arguments
    ///     * use DEFAULT_TLS_PORT
    #[clap(short, name="port", required(false), help="Specifies the TCP port that the server is listening on")]
    #[clap(hide_default_value(true), default_value(DEFAULT_PORT), default_value_if("encrypt", None, Some(DEFAULT_TLS_PORT)))]
    pub port: u16,

    #[clap(name="hostname", required(true), help="Specifies the name of the server (either DNS or IP address in dotted notation)")]
    pub hostname: String,

    #[clap(name="Northeastern-username", required(true))]
    pub username: String,

    #[clap(short='w', long, required(false), help="Define a path to a list of words")]
    #[clap(hide(true), parse(try_from_str=validate_path), default_value(DEFAULT_WORD_LIST_PATH))]
    pub word_list: PathBuf
}

fn validate_path(string_path: &str) -> Result<PathBuf, String> {
    let path = PathBuf::from(string_path);

    match path.exists() {
        true => Ok(path),
        false => Err(String::from(format!("No file exists at {:?}", path.display())))
    }
}