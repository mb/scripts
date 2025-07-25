use serde::{Serialize, Serializer};
use serde_json::Value;
use std::{cmp::Ordering, collections::BTreeMap, env};
use url::Url;

#[derive(Debug, Clone, Eq, PartialEq, PartialOrd, Hash)]
struct BugzillaKey(String);

fn is_advanced(s: &str) -> Option<i32> {
    let (head, tail) = s.split_at_checked(1)?;
    let add = match head {
        "v" => 0,
        "o" => 1,
        "f" => 2,
        _ => return None,
    };
    if head != "v" && head != "o" && head != "f" {
        return None;
    }
    let i = tail.parse::<i32>().ok()?;
    i.checked_mul(3)?.checked_add(add)
}

fn presort_fields(field: &str) -> i32 {
    match field {
        "product" => 1,
        "component" => 2,
        "status" => 3,
        "resolution" => 4,
        "query_format" => 2000,
        _ => 1000,
    }
}

impl Ord for BugzillaKey {
    fn cmp(&self, other: &Self) -> Ordering {
        match (is_advanced(&self.0), is_advanced(&other.0)) {
            (None, None) => {
                // put some to the top of the list, some to the bottom
                match presort_fields(&self.0).cmp(&presort_fields(&other.0)) {
                    Ordering::Equal => self.0.cmp(&other.0),
                    other => other,
                }
            }
            (Some(_), None) => Ordering::Greater,
            (None, Some(_)) => Ordering::Less,
            (Some(i), Some(j)) => i.cmp(&j),
        }
    }
}

impl Serialize for BugzillaKey {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.0)
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 2 {
        eprintln!("Usage: {} <url>", args[0]);
        eprintln!("Pass Bugzilla URL from advanced search to convert to rest API JSON");
        std::process::exit(1);
    }

    let url = Url::parse(&args[1]).expect("Argument is not an URL");

    // stable output order
    let mut map = BTreeMap::new();
    for (key, value) in url.query_pairs() {
        if key == "query_based_on"
            || key == "list_id"
            || key == "classification"
            || key == "known_name"
        {
            continue;
        }
        let key = BugzillaKey(key.to_string());
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
