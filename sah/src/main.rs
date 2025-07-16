//! Example application for testing Storage-Access-Headers and also difference to Storage-Access API
//!
//! Login-Scenario with iframes
//!
//! Endpoints:
//! Initialize state:
//! * track -> sets state without user interaction if not yet initialized
//! * auth -> needs interaction for auth
//! Access state:
//! * iframe.html -> just returns the headers
//! * image.png -> renders the request headers in an png and returns them
//! * script.js -> modifies the div with id="storage-access-headers" to contain the request headers
//! * style.css -> modifies some spans with :after { content: "..." } to the request headers
//!
//! * iframe-auth -> expects to be embedded, tries to get unpartitioned storage access
//! * iframe-track -> tries to set unpartitioned state
//! * script-track -> tries to set unpartitioned state
//! * image-track -> tries to set unpartitioned state

use warp::{
    Filter,
    filters::path::Tail,
    http::StatusCode,
    reply::{self, Reply, Response},
};

struct Request {
    cookie: Option<String>,
    permission_policy: Option<String>,
    sec_fetch_storage_access: Option<String>,
}

impl Request {
    fn main(&self) -> Response {
        let response = format!(
            r#"<!DOCTYPE html>
            <html>
                <head><title>Storage-Access-API test ground</title></head>
                <body>
                    <h1>Storage-Access-API test ground</h1>
                    <a href="https://lab.yet.wiki/storage-access/
                    <h2>Main document headers</h2>
                    <p>Cookie: <span class="cookie">{cookie:?}</span></p>
                    <p>Permission-Policy: <span class="pp">{permission_policy:?}</span></p>
                    <p>Sec-Fetch-Storage-Access: <span class="sah">{sec_fetch_storage_access:?}</span></p>
                    <h2>CSS headers</h2>
                    <link href="https://lab.yet.wiki/storage-access/style.css" rel="stylesheet" />
                    <p>Cookie: <span id="css-cookie" class="cookie"></span></p>
                    <p>Permission-Policy: <span id="css-pp" class="pp"></span></p>
                    <p>Sec-Fetch-Storage-Access: <span id="css-sah" class="sah"></span></p>
                    <h2>Script headers</h2>
                    <p>Cookie: <span id="js-cookie" class="cookie"></span></p>
                    <p>Permission-Policy: <span id="js-pp" class="pp"></span></p>
                    <p>Sec-Fetch-Storage-Access: <span id="js-sah" class="sah"></span></p>
                    <h2>Image headers</h2>
                    <img src="https://lab.yet.wiki/storage-access/image.png"></img>
                    <h2>Iframe headers</h2>
                    <iframe src="https://lab.yet.wiki/storage-access/iframe.html"></iframe>
                </body>
            </html>"#,
            cookie = self.cookie,
            permission_policy = self.permission_policy,
            sec_fetch_storage_access = self.sec_fetch_storage_access,
        );
        warp::reply::html(response).into_response()
    }

    pub fn respond(&self, endpoint: Tail) -> Response {
        let (endpoint, query) = if let Some((endpoint, data)) =
            endpoint.as_str().split_once(|c| c == '/' || c == '?')
        {
            (endpoint, Some(data))
        } else {
            // no further data in url
            (endpoint.as_str(), None)
        };

        match endpoint {
            "" => self.main(),
            _ => reply::with_status(
                format!("Not found! \"{endpoint:?}\""),
                StatusCode::NOT_FOUND,
            )
            .into_response(),
        }
    }
}

#[tokio::main]
async fn main() {
    let sah = warp::path("storage-access")
        .and(warp::path::tail())
        .and(warp::header::optional("cookie"))
        // https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy/storage-access
        .and(warp::header::optional("permission-policy"))
        // storage-access-header request
        .and(warp::header::optional("sec-fetch-storage-access"))
        .map(
            |endpoint, cookie, permission_policy, sec_fetch_storage_access| {
                Request {
                    cookie,
                    permission_policy,
                    sec_fetch_storage_access,
                }
                .respond(endpoint)
            },
        );

    warp::serve(sah).run(([127, 0, 0, 1], 3030)).await;

    println!("Hello, world!");
}
