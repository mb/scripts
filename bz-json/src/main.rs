use percent_encoding::{percent_encode, utf8_percent_encode, NON_ALPHANUMERIC};
use serde::{Serialize, Serializer};
use serde_json::Value;
use std::{cmp::Ordering, collections::BTreeMap, env};
use url::{EncodingOverride, Url};

#[derive(Debug, Clone, Eq, PartialEq, PartialOrd, Hash)]
struct BugzillaKey(String);

fn is_advanced(s: &str) -> Option<i32> {
    let (head, tail) = s.split_at_checked(1)?;
    let add = match head {
        "v" => 0,
        "o" => 1,
        "f" => 2,
        "j" => 3,
        _ => return None,
    };
    let i = tail.parse::<i32>().ok()?;
    i.checked_mul(4)?.checked_add(add)
}

fn presort_fields(field: &str) -> i32 {
    match field {
        "query_based_on" => 0,
        "product" => 1,
        "component" => 2,
        "status" => 3,
        "resolution" => 4,
        "query_format" => 2000,
        "j_top" => 2001,
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
    let mut out_url = url.clone();

    // stable output order
    let mut map = BTreeMap::new();
    for (key, value) in url.query_pairs() {
        if key == "list_id" || key == "classification" || key == "known_name" {
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
    {
        let mut out_query = out_url.query_pairs_mut();
        out_query.clear();
        // sort array and also output more beautiful URL
        for (key, value) in &mut map {
            match value {
                Value::String(ref s) => {
                    out_query.append_pair(&key.0, &s);
                }
                Value::Array(ref mut values) => {
                    values.sort_by(|s1, s2| match (s1, s2) {
                        (Value::String(s1), Value::String(s2)) => s1.cmp(s2),
                        _ => unreachable!("only strings should be in the array"),
                    });
                    for v in values.iter() {
                        match v {
                            Value::String(s) => {
                                out_query.append_pair(&key.0, &s);
                            }
                            _ => unreachable!("only strings should be in the array"),
                        }
                    }
                }
                _ => panic!("unreachable"),
            }
        }
        out_query.finish();
    }

    println!("{out_url}");
    println!("{}", serde_json::to_string_pretty(&map).unwrap());
}
