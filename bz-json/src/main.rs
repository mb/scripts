use serde_json::Value;
use std::env;
use url::Url;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 2 {
        eprintln!("Usage: {} <url>", args[0]);
        eprintln!("Pass Bugzilla URL from advanced search to convert to rest API JSON");
        std::process::exit(1);
    }

    let url = Url::parse(&args[1]).expect("Argument is not an URL");

    // stable output order
    let mut map = indexmap::IndexMap::new();
    for (key, value) in url.query_pairs() {
        if let Some(existing) = map.get_mut(&key) {
            match existing {
                Value::Array(arr) => arr.push(Value::String(value.to_string())),
                Value::String(str) => {
                    *existing = Value::Array(vec![
                        Value::String(str.clone()),
                        Value::String(value.to_string()),
                    ])
                }
                _ => panic!("unreachable"),
            }
        } else {
            map.insert(key, Value::String(value.to_string()));
        }
    }

    println!("{}", serde_json::to_string_pretty(&map).unwrap());
}
