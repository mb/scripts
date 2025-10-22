use std::collections::HashSet;

use clap::Parser;
use serde::{Deserialize, Serialize};
use serde_json::to_string;

const DEV_SERVER_LOCATION: &'static str = "https://remote-settings-dev.allizom.org/v1";
const STAGE_SERVER_LOCATION: &'static str = "https://remote-settings.allizom.org/v1";
const PROD_SERVER_LOCATION: &'static str = "https://remote-settings.mozilla.org/v1";

const REMOTE_SETTINGS_BUCKET: &'static str = "main-workspace";
const REMOTE_SETTINGS_COLLECTION: &'static str = "url-classifier-exceptions";

const PROD_RECORDS_LOCATION: &'static str = "https://firefox.settings.services.mozilla.com/v1/buckets/main/collections/url-classifier-exceptions/records";

#[derive(Deserialize, Debug)]
struct BlockingBugsResponse {
    bugs: Vec<BlockingBug>,
}

#[derive(Deserialize, Debug)]
struct BlockingBug {
    id: u32,
    summary: String,
    depends_on: Vec<u32>,
    blocks: Vec<u32>,
}

// All breakage bugs
const BUGS: [u32; 80] = [
    1850793, 1962725, 1963384, 1960872, 1971535, 1963418, 1869585, 1963419, 1962722, 1963377,
    1963387, 1962713, 1962711, 1963416, 1866290, 1949475, 1962673, 1960877, 1962724, 1962718,
    1960868, 1894088, 1969882, 1963420, 1963391, 1960874, 1963422, 1970377, 1962719, 1963382,
    1963311, 1962716, 1962367, 1963380, 1963370, 1962727, 1963389, 1963379, 1944074, 1962721,
    1962463, 1962723, 1963417, 1740763, 1968970, 1963376, 1963386, 1962712, 1960862, 1962564,
    1839375, 1970603, 1963414, 1853117, 1972018, 1963388, 1963378, 1960865, 1960871, 1962715,
    1962717, 1944781, 1963390, 1963421, 1963423, 1962726, 1963392, 1973175, 1973185, 1969919,
    1960851, 1962729, 1960878, 1963381, 1963383, 1772545, 1962728, 1962714, 1940042, 1962443,
];

fn retrieve_blocking_bugs() -> Vec<BlockingBug> {
    let bugs: String = BUGS
        .iter()
        .map(|i| i.to_string())
        .collect::<Vec<_>>()
        .join(",");
    let url = format!(
        "https://bugzilla.mozilla.org/rest/bug?\
        include_fields=id,blocks,depends_on,summary&\
        id={}",
        bugs
    );

    println!("Bugzilla query: {url}");
    let response = reqwest::blocking::get(url)
        .expect("bugzilla: failed to request bugs")
        .json::<BlockingBugsResponse>()
        .expect("bugzilla: no response");
    response.bugs
}

#[derive(Parser)]
struct Args {
    #[arg(long)]
    prod: bool,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct BlockEntry {
    bug_ids: Vec<String>,
    schema: u64,
    category: String,
    url_pattern: String,
    #[serde(rename = "filter_expression")]
    #[serde(default)]
    #[serde(skip_serializing_if = "Option::is_none")]
    filter_expression: Option<String>,
    classifier_features: Vec<String>,
    #[serde(default)]
    #[serde(skip_serializing_if = "Option::is_none")]
    top_level_url_pattern: Option<String>,
    #[serde(default)]
    #[serde(skip_serializing_if = "Option::is_none")]
    is_private_browsing_only: Option<bool>,
    #[serde(default)]
    #[serde(skip_serializing_if = "Option::is_none")]
    filter_content_blocking_categories: Option<Vec<String>>,
    id: String,
    #[serde(rename = "last_modified")]
    last_modified: u64,
}

#[derive(Deserialize, Debug)]
struct Records {
    data: Vec<BlockEntry>,
}

fn get_current_list() -> Records {
    reqwest::blocking::get(PROD_RECORDS_LOCATION)
        .expect("Failed to load")
        .json::<Records>()
        .expect("wrong schema")
}
/*/
fn update(args: &Args, record: BlockEntry) {
    let server = if args.prod {
        PROD_SERVER_LOCATION
    } else {
        STAGE_SERVER_LOCATION
    };
    let id = &record.id;
    let url = format!(
        "{server}/buckets/{REMOTE_SETTINGS_BUCKET}/collections/{REMOTE_SETTINGS_COLLECTION}/records/{id}"
    );

    let c = reqwest::blocking::Client::new();
    let request = c
        .post(url)
        .json(&record)
        .bearer_auth(&args.auth_token)
        .build()
        .expect("failed to update remote settings");
    let response = request.body().expect("expected resonponse");
    println!("{response:?}");
}
*/

fn get_changes(blocking_bugs: &[BlockingBug], entries: &[BlockEntry]) {
    let bugs: HashSet<u32> = BUGS.iter().cloned().collect();
    for e in entries {
        for id in &e.bug_ids {
            let id = id.parse::<u32>().unwrap();
            if bugs.contains(&id) {
                println!("{e:?}");
                println!("https://bugzil.la/{id}");
            }
        }
    }
}

fn main() {
    //let args = Args::parse();
    let blocking_bugs = retrieve_blocking_bugs();
    println!("{blocking_bugs:?}");
    for (idx, b) in blocking_bugs.iter().enumerate() {
        assert_eq!(b.blocks, &[1537702]);
        let depends_on = b
            .depends_on
            .iter()
            .map(|i| i.to_string())
            .collect::<Vec<_>>();
        println!(
            "{}. {}: {} (https://bugzil.la/{} - {})",
            idx,
            b.id,
            depends_on.join(" "),
            b.id,
            b.summary
        );
        println!(
            "  \"bugIds\": [\n    \"{}\"\n  ],",
            depends_on.join("\",\n    \"")
        );
    }
    /*
    let cur_entries = get_current_list();
    get_changes(&blocking_bugs, &cur_entries.data);
    */
}
