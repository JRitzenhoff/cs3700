pub mod cmdline;
pub mod remote;

pub fn hello_world(name: String) {
    println!("Hello World {}", name);    
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        let result = 2 + 2;
        assert_eq!(result, 4);
    }
}
