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
//! * fetch.json -> just returns it as json
//!
//! * iframe-auth -> expects to be embedded, tries to get unpartitioned storage access
//! * iframe-track -> tries to set unpartitioned state
//! * script-track -> tries to set unpartitioned state
//! * image-track -> tries to set unpartitioned state

use text_to_png::TextRenderer;
use warp::{
    Filter,
    filters::path::Tail,
    http::StatusCode,
    reply::{self, Reply, Response},
};

struct Request {
    host: Option<String>,
    cookie: Option<String>,
    permission_policy: Option<String>,
    referer: Option<String>,
    origin: Option<String>,
    sec_fetch_storage_access: Option<String>,
}

enum Header {
    Host,
    Cookie,
    PermissionPolicy,
    Referer,
    Origin,
    SecFetchStorageAccess,
}

enum Escape {
    None,
    Css,
    Json,
    Html,
}

impl Request {
    fn get(&self, header: Header, escape: Escape) -> String {
        let header = match header {
            Header::Host => self.host.as_ref(),
            Header::Cookie => self.cookie.as_ref(),
            Header::PermissionPolicy => self.permission_policy.as_ref(),
            Header::Referer => self.referer.as_ref(),
            Header::Origin => self.origin.as_ref(),
            Header::SecFetchStorageAccess => self.sec_fetch_storage_access.as_ref(),
        };
        match escape {
            Escape::None => header
                .map(|el| format!("{:?}", el))
                .unwrap_or("null".to_owned()),
            Escape::Json => {
                // quote quotation marks and string first
                let s = header
                    .map(|el| format!("{:?}", el))
                    .unwrap_or("null".to_owned());
                // then encode as json
                serde_json::to_string(&s).unwrap()
            }
            Escape::Css => header
                .map(|el| format!("'{:?}'", el.replace('\'', "\\'")))
                .unwrap_or("'null'".to_owned()),
            Escape::Html => {
                let unescaped = header
                    .map(|el| format!("{:?}", el))
                    .unwrap_or("null".to_owned());
                html_escape::encode_text(&unescaped).to_string()
            }
        }
    }
}

impl Request {
    fn main(&self, iframe: bool) -> Response {
        let domain = "https://sah.neon.rocks/storage-access";
        let iframe_embed = if !iframe {
            format!(
                r#"
                    <h2>Iframe headers <small>({domain}/iframe.html)</small></h2>
                    <iframe src="{domain}/iframe.html" width="100%" height="2000"></iframe>
                "#,
            )
        } else {
            String::new()
        };
        let response = format!(
            r#"<!DOCTYPE html>
            <html>
                <head><title>Storage-Access-API test ground</title></head>
                <body>
                    <h1>Storage-Access-API test ground</h1>
                    If a header doesn't exist, null will be displayed. If it has a value, an additional round of quotes (&quot;) will be displayed.<br>
                    Links to set unpartitioned storage on the third party domain:
                    <ul>
                        <li><a href="{domain}/auth">Auth</a></li>
                        <li><a href="{domain}/track">Track</a></li>
                    </ul>
                    <h2>Main document headers</h2>
                    <p>Host: <span class="cookie">{host}</span></p>
                    <p>Origin: <span class="origin">{origin}</span></p>
                    <p>Referer: <span class="referer">{referer}</span></p>
                    <p>Cookie: <span class="cookie">{cookie}</span></p>
                    <p>Permission-Policy: <span class="pp">{permission_policy}</span></p>
                    <p>Sec-Fetch-Storage-Access: <span class="sah">{sec_fetch_storage_access}</span></p>
                    <h2>Fetch headers <small>({domain}/fetch.json)</small></h2>
                    <p>Host: <span id="fetch-host" class="host"></span></p>
                    <p>Origin: <span id="fetch-origin" class="origin"></span></p>
                    <p>Referer: <span id="fetch-referer" class="referer"></span></p>
                    <p>Cookie: <span id="fetch-cookie" class="cookie"></span></p>
                    <p>Permission-Policy: <span id="fetch-pp" class="pp"></span></p>
                    <p>Sec-Fetch-Storage-Access: <span id="fetch-sah" class="sah"></span></p>
                    <script>
                        let host = document.getElementById("fetch-host");
                        let origin = document.getElementById("fetch-origin");
                        let referer = document.getElementById("fetch-referer");
                        let cookie = document.getElementById("fetch-cookie");
                        let pp = document.getElementById("fetch-pp");
                        let sah = document.getElementById("fetch-sah");
                        fetch("{domain}/fetch.json")
                            .then((response) => response.json())
                            .then((response) => {{
                                host.innerText = response.host;
                                origin.innerText = response.origin;
                                referer.innerText = response.referer;
                                cookie.innerText = response.cookie;
                                pp.innerText = response.permission_policy;
                                sah.innerText = response.sec_fetch_storage_access;
                            }});
                    </script>
                    <h2>CSS headers <small>({domain}/style.css)</small></h2>
                    <link href="{domain}/style.css" rel="stylesheet" />
                    <p>Host: <span id="css-host" class="host"></span></p>
                    <p>Origin: <span id="css-origin" class="origin"></span></p>
                    <p>Referer: <span id="css-referer" class="referer"></span></p>
                    <p>Cookie: <span id="css-cookie" class="cookie"></span></p>
                    <p>Permission-Policy: <span id="css-pp" class="pp"></span></p>
                    <p>Sec-Fetch-Storage-Access: <span id="css-sah" class="sah"></span></p>
                    <h2>Script headers <small>({domain}/script.js)</small></h2>
                    <p>Host: <span id="js-host" class="host"></span></p>
                    <p>Origin: <span id="js-origin" class="origin"></span></p>
                    <p>Referer: <span id="js-referer" class="referer"></span></p>
                    <p>Cookie: <span id="js-cookie" class="cookie"></span></p>
                    <p>Permission-Policy: <span id="js-pp" class="pp"></span></p>
                    <p>Sec-Fetch-Storage-Access: <span id="js-sah" class="sah"></span></p>
                    <script src="{domain}/script.js"></script>
                    <h2>Image headers <small>({domain}/image.png)</small></h2>
                    <img src="{domain}/image.png"></img>
                    {iframe_embed}
                </body>
            </html>"#,
            host = self.get(Header::Host, Escape::Html),
            origin = self.get(Header::Origin, Escape::Html),
            referer = self.get(Header::Referer, Escape::Html),
            cookie = self.get(Header::Cookie, Escape::Html),
            permission_policy = self.get(Header::PermissionPolicy, Escape::Html),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Html),
        );
        warp::reply::html(response).into_response()
    }

    fn css(&self) -> Response {
        let response = format!(
            r#"
                #css-host::after {{
                    content: {host};
                }}
                #css-origin::after {{
                    content: {origin};
                }}
                #css-referer::after {{
                    content: {referer};
                }}
                #css-cookie::after {{
                    content: {cookie};
                }}
                #css-pp::after {{
                    content: {permission_policy};
                }}
                #css-sah::after {{
                    content: {sec_fetch_storage_access};
                }}
            "#,
            host = self.get(Header::Host, Escape::Css),
            origin = self.get(Header::Origin, Escape::Css),
            referer = self.get(Header::Referer, Escape::Css),
            cookie = self.get(Header::Cookie, Escape::Css),
            permission_policy = self.get(Header::PermissionPolicy, Escape::Css),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Css),
        );
        warp::reply::with_header(response, "content-type", "text/css").into_response()
    }

    fn js(&self) -> Response {
        let response = format!(
            r#"
                document.getElementById("js-host").innerText = {host}
                document.getElementById("js-origin").innerText = {origin}
                document.getElementById("js-referer").innerText = {referer}
                document.getElementById("js-cookie").innerText = {cookie}
                document.getElementById("js-pp").innerText = {permission_policy}
                document.getElementById("js-sah").innerText = {sec_fetch_storage_access}
            "#,
            host = self.get(Header::Host, Escape::Css),
            origin = self.get(Header::Origin, Escape::Css),
            referer = self.get(Header::Referer, Escape::Css),
            cookie = self.get(Header::Cookie, Escape::Css),
            permission_policy = self.get(Header::PermissionPolicy, Escape::Css),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Css),
        );
        warp::reply::with_header(response, "content-type", "text/javascript").into_response()
    }

    fn json(&self) -> Response {
        let response = format!(
            r#"
                {{
                    "host": {host},
                    "origin": {origin},
                    "referer": {referer},
                    "cookie": {cookie},
                    "permission_policy": {permission_policy},
                    "sec_fetch_storage_access": {sec_fetch_storage_access}
                }}
            "#,
            host = self.get(Header::Host, Escape::Json),
            origin = self.get(Header::Origin, Escape::Json),
            referer = self.get(Header::Referer, Escape::Json),
            cookie = self.get(Header::Cookie, Escape::Json),
            permission_policy = self.get(Header::PermissionPolicy, Escape::Json),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Json),
        );
        let mut response =
            warp::reply::with_header(response, "content-type", "application/json").into_response();

        if let Some(origin) = self.origin.as_ref() {
            if let Ok(host) = origin.parse() {
                response
                    .headers_mut()
                    .append("access-control-allow-origin", host);
            }
        }
        response
    }

    fn png(&self) -> Response {
        // TODO: multiline text with imageproc?
        // https://github.com/RookAndPawn/text-to-png/issues/3
        let response = format!(
            "\
                Host: {host}, \
                Origin: {origin}, \
                Referer: {referer}, \
                Cookie: {cookie}, \
                Permission-Policy: {permission_policy}, \
                Sec-Fetch-Storage-Access: {sec_fetch_storage_access}\
            ",
            host = self.get(Header::Host, Escape::None),
            origin = self.get(Header::Origin, Escape::None),
            referer = self.get(Header::Referer, Escape::None),
            cookie = self.get(Header::Cookie, Escape::None),
            permission_policy = self.get(Header::PermissionPolicy, Escape::None),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::None),
        );
        let renderer = TextRenderer::default();
        let text_png = renderer
            .render_text_to_png_data(response, 16, "#000000")
            .unwrap();
        warp::reply::with_header(text_png.data, "content-type", "image/png").into_response()
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
            "" => self.main(false),
            "style.css" => self.css(),
            "script.js" => self.js(),
            "fetch.json" => self.json(),
            "image.png" => self.png(),
            "iframe.html" => self.main(true),
            _ => reply::with_status(format!("Not found! {endpoint:?}"), StatusCode::NOT_FOUND)
                .into_response(),
        }
    }
}

#[tokio::main]
async fn main() {
    let sah = warp::path("storage-access")
        .and(warp::path::tail())
        .and(warp::header::optional("host"))
        .and(warp::header::optional("origin"))
        .and(warp::header::optional("referer"))
        .and(warp::header::optional("cookie"))
        // https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy/storage-access
        .and(warp::header::optional("permission-policy"))
        // storage-access-header request
        .and(warp::header::optional("sec-fetch-storage-access"))
        .map(
            |endpoint,
             host,
             origin,
             referer,
             cookie,
             permission_policy,
             sec_fetch_storage_access| {
                Request {
                    host,
                    origin,
                    referer,
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
