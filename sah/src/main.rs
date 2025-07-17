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

use cookie::Cookie;
use text_to_png::TextRenderer;
use url::Url;
use uuid::Uuid;
use warp::{
    Filter,
    filters::path::Tail,
    http::StatusCode,
    hyper::Body,
    reply::{self, Reply, Response},
};

struct Request {
    host: Option<String>,
    cookie: Option<String>,
    referer: Option<String>,
    origin: Option<String>,
    sec_fetch_storage_access: Option<String>,
}

enum Header {
    Host,
    Cookie,
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
    fn get_host_ident(&self) -> &'static str {
        if let Some(host) = self.host.as_ref() {
            match host.as_str() {
                "sah.yet.wiki" => "wiki",
                "sah.yet.cx" => "cx",
                "sah.neon.rocks" => "neon",
                _ => "none",
            }
        } else {
            "none"
        }
    }
    fn style(&self) -> String {
        let background_color = if let Some(host) = self.host.as_ref() {
            match host.as_str() {
                "sah.yet.wiki" => "99c1f1",
                "sah.yet.cx" => "f9f06b",
                "sah.neon.rocks" => "f66151",
                _ => "ffffff",
            }
        } else {
            "ffffff"
        };
        format!(
            "<style>
                body {{
                    background-color: {background_color};
                }}
                p {{
                    margin: 0;
                }}
            </style>"
        )
    }
    // simulate SSO auth flow with user interaction
    fn auth(&self) -> Response {
        let style = self.style();
        let response = format!(
            r#"<!DOCTYPE html>
            <html>
                <head><title>Storage-Access-API test ground</title></head>
                {style}
                <body>
                    <h1>Storage-Access-API test ground</h1>
                    If a header doesn't exist, null will be displayed. If it has a value, an additional round of quotes (&quot;) will be displayed.<br>
                    Links to set unpartitioned storage on the third party domain:

                    <form>
                        <label for="username">Username:</label><br>
                        <input type="text" id="username" name="username"><br><br>
                        <label for="password">Password:</label><br>
                        <input type="password" id="password" name="password"><br><br>
                        <input type="submit" value="Submit" formaction="track">
                    </form>
                    <h2>Main document headers</h2>
                    <p>Host: <span class="cookie">{host}</span></p>
                    <p>Origin: <span class="origin">{origin}</span></p>
                    <p>Referer: <span class="referer">{referer}</span></p>
                    <p>Cookie: <span class="cookie">{cookie}</span></p>
                    <p>Sec-Fetch-Storage-Access: <span class="sah">{sec_fetch_storage_access}</span></p>
                </body>
            </html>"#,
            host = self.get(Header::Host, Escape::Html),
            origin = self.get(Header::Origin, Escape::Html),
            referer = self.get(Header::Referer, Escape::Html),
            cookie = self.get(Header::Cookie, Escape::Html),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Html),
        );
        warp::reply::html(response).into_response()
    }
    // simulate bounce tracking without user interaction
    fn track(&self) -> Response {
        let mut id = None;
        // parse current id
        if let Some(cookies) = self.cookie.as_ref() {
            for cookie in Cookie::split_parse(cookies) {
                if let Ok(cookie) = cookie {
                    match cookie.name() {
                        "id" => {
                            if let Ok(uuid) = Uuid::parse_str(cookie.value()) {
                                id = Some(uuid)
                            }
                            break;
                        }
                        _ => continue,
                    }
                }
            }
        }
        // forward current id via url param and store as cookie if it didn't exist
        if let Some(id) = id {
            warp::http::Response::builder()
                .header(
                    "Location",
                    &format!("https://sah.yet.wiki/storage-access?id={id}"),
                )
                .status(307)
                .body(Body::empty())
                .unwrap()
        } else {
            let id = uuid::Uuid::now_v7();
            warp::http::Response::builder()
                .header(
                    "Location",
                    &format!("https://sah.yet.wiki/storage-access?id={id}"),
                )
                .header("Set-Cookie", &format!("id={id}; Secure; HttpOnly"))
                .status(307)
                .body(Body::empty())
                .unwrap()
        }
    }
    fn table(req: &str) -> String {
        format!(
            r#"
            <table>
                <thead>
                    <tr>
                        <td></td>
                        <td>neon.rocks</td>
                        <td>yet.wiki</td>
                        <td>yet.cx</td>
                    </tr>
                </thead>
                <tr>
                    <td>host</td>
                    <td><span id="neon-{req}-host" class="host"></span></td>
                    <td><span id="wiki-{req}-host" class="host"></span></td>
                    <td><span id="cx-{req}-host" class="host"></span></td>
                </tr>
                <tr>
                    <td>origin</td>
                    <td><span id="neon-{req}-origin" class="origin"></span></td>
                    <td><span id="wiki-{req}-origin" class="origin"></span></td>
                    <td><span id="cx-{req}-origin" class="origin"></span></td>
                </tr>
                <tr>
                    <td>referer</td>
                    <td><span id="neon-{req}-referer" class="referer"></span></td>
                    <td><span id="wiki-{req}-referer" class="referer"></span></td>
                    <td><span id="cx-{req}-referer" class="referer"></span></td>
                </tr>
                <tr>
                    <td>cookie</td>
                    <td><span id="neon-{req}-cookie" class="cookie"></span></td>
                    <td><span id="wiki-{req}-cookie" class="cookie"></span></td>
                    <td><span id="cx-{req}-cookie" class="cookie"></span></td>
                </tr>
                <tr>
                    <td>sec-fetch-storage-access</td>
                    <td><span id="neon-{req}-sah" class="host"></span></td>
                    <td><span id="wiki-{req}-sah" class="host"></span></td>
                    <td><span id="cx-{req}-sah" class="host"></span></td>
                </tr>
            </table>
            "#
        )
    }
}

impl Request {
    fn main(&self, iframe: bool) -> Response {
        let domain = "https://sah.neon.rocks/storage-access";
        let style = self.style();
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
        let fetch = Request::table("fetch");
        let css = Request::table("css");
        let js = Request::table("js");
        let response = format!(
            r#"<!DOCTYPE html>
            <html>
                <head><title>Storage-Access-API test ground</title></head>
                <body>
                    {style}
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
                    <p>Sec-Fetch-Storage-Access: <span class="sah">{sec_fetch_storage_access}</span></p>
                    <h2>Fetch headers <small>({domain}/fetch.json)</small></h2>
                    {fetch}
                    <script>
                        let headers = ["host", "origin", "referer", "cookie", "sah"];
                        fetch("https://sah.neon.rocks/storage-access/fetch.json")
                            .then((response) => response.json())
                            .then((response) => {{
                                for (const header in headers) {{
                                    console.log(headers[header]);
                                    document.getElementById("neon-fetch-"+headers[header]).innerText = response[headers[header]];
                                }}
                            }})
                        fetch("https://sah.yet.wiki/storage-access/fetch.json")
                            .then((response) => response.json())
                            .then((response) => {{
                                for (const header in headers) {{
                                    console.log(headers[header]);
                                    document.getElementById("wiki-fetch-"+headers[header]).innerText = response[headers[header]];
                                }}
                            }})
                        fetch("https://sah.yet.cx/storage-access/fetch.json")
                            .then((response) => response.json())
                            .then((response) => {{
                                for (const header in headers) {{
                                    console.log(headers[header]);
                                    document.getElementById("cx-fetch-"+headers[header]).innerText = response[headers[header]];
                                }}
                            }})
                    </script>
                    <h2>CSS headers <small>({domain}/style.css)</small></h2>
                    {css}
                    <link href="https://sah.neon.rocks/storage-access/style.css" rel="stylesheet" />
                    <link href="https://sah.yet.wiki/storage-access/style.css" rel="stylesheet" />
                    <link href="https://sah.yet.cx/storage-access/style.css" rel="stylesheet" />
                    <h2>Script headers <small>({domain}/script.js)</small></h2>
                    {js}
                    <script src="https://sah.neon.rocks/storage-access/script.js"></script>
                    <script src="https://sah.yet.wiki/storage-access/script.js"></script>
                    <script src="https://sah.yet.cx/storage-access/script.js"></script>
                    <h2>Image headers <small>({domain}/image.png)</small></h2>
                    <p><img src="https://sah.neon.rocks/storage-access/image.png"></img></p>
                    <p><img src="https://sah.yet.wiki/storage-access/image.png"></img></p>
                    <p><img src="https://sah.yet.cx/storage-access/image.png"></img></p>
                    {iframe_embed}
                </body>
            </html>"#,
            host = self.get(Header::Host, Escape::Html),
            origin = self.get(Header::Origin, Escape::Html),
            referer = self.get(Header::Referer, Escape::Html),
            cookie = self.get(Header::Cookie, Escape::Html),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Html),
        );
        warp::reply::html(response).into_response()
    }

    fn css(&self) -> Response {
        let ident = self.get_host_ident();
        let response = format!(
            r#"
                #{ident}-css-host::after {{
                    content: {host};
                }}
                #{ident}-css-origin::after {{
                    content: {origin};
                }}
                #{ident}-css-referer::after {{
                    content: {referer};
                }}
                #{ident}-css-cookie::after {{
                    content: {cookie};
                }}
                #{ident}-css-sah::after {{
                    content: {sec_fetch_storage_access};
                }}
            "#,
            host = self.get(Header::Host, Escape::Css),
            origin = self.get(Header::Origin, Escape::Css),
            referer = self.get(Header::Referer, Escape::Css),
            cookie = self.get(Header::Cookie, Escape::Css),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::Css),
        );
        warp::reply::with_header(response, "content-type", "text/css").into_response()
    }

    fn js(&self) -> Response {
        let ident = self.get_host_ident();
        let response = format!(
            r#"
                document.getElementById("{ident}-js-host").innerText = {host}
                document.getElementById("{ident}-js-origin").innerText = {origin}
                document.getElementById("{ident}-js-referer").innerText = {referer}
                document.getElementById("{ident}-js-cookie").innerText = {cookie}
                document.getElementById("{ident}-js-sah").innerText = {sec_fetch_storage_access}
            "#,
            host = self.get(Header::Host, Escape::Css),
            origin = self.get(Header::Origin, Escape::Css),
            referer = self.get(Header::Referer, Escape::Css),
            cookie = self.get(Header::Cookie, Escape::Css),
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
                    "sah": {sec_fetch_storage_access}
                }}
            "#,
            host = self.get(Header::Host, Escape::Json),
            origin = self.get(Header::Origin, Escape::Json),
            referer = self.get(Header::Referer, Escape::Json),
            cookie = self.get(Header::Cookie, Escape::Json),
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
                Sec-Fetch-Storage-Access: {sec_fetch_storage_access}\
            ",
            host = self.get(Header::Host, Escape::None),
            origin = self.get(Header::Origin, Escape::None),
            referer = self.get(Header::Referer, Escape::None),
            cookie = self.get(Header::Cookie, Escape::None),
            sec_fetch_storage_access = self.get(Header::SecFetchStorageAccess, Escape::None),
        );
        let renderer = TextRenderer::default();
        let text_png = renderer
            .render_text_to_png_data(response, 16, "#000000")
            .unwrap();
        warp::reply::with_header(text_png.data, "content-type", "image/png").into_response()
    }

    /// store id from query parameter in cookie and redirect to url without query param
    fn store_id(&self, endpoint: &Tail) -> Option<Response> {
        /*
        let host = self.host.as_ref()?;
        let url = format!("https://{host}/storage-access/{}", endpoint.as_str());
        let url = Url::parse(&url).ok()?;
        let mut id = None;
        // find id parameter
        for (name, value) in url.query_pairs() {
            if name == "id" {
                id = Some(value);
                break;
            }
        }
        if let Some(id) = id {
            let mut out_params = url_out.as_mut().map(|url| {
                let mut out_params = url.query_pairs_mut();
                out_params.clear();
                out_params
            });


        } else {
            None
        }
        */
        None
    }

    pub fn respond(&self, endpoint: Tail) -> Response {
        if let Some(response) = self.store_id(&endpoint) {
            return response;
        }
        let (endpoint, query) = if let Some((endpoint, data)) =
            endpoint.as_str().split_once(|c| c == '/' || c == '?')
        {
            (endpoint, Some(data))
        } else {
            // no further data in url
            (endpoint.as_str(), None)
        };

        match endpoint {
            // information
            "" => self.main(false),
            "style.css" => self.css(),
            "script.js" => self.js(),
            "fetch.json" => self.json(),
            "image.png" => self.png(),
            "iframe.html" => self.main(true),
            // track
            "auth" => self.auth(),
            "track" => self.track(),
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
        // storage-access-header request
        .and(warp::header::optional("sec-fetch-storage-access"))
        .map(
            |endpoint, host, origin, referer, cookie, sec_fetch_storage_access| {
                Request {
                    host,
                    origin,
                    referer,
                    cookie,
                    sec_fetch_storage_access,
                }
                .respond(endpoint)
            },
        );

    warp::serve(sah).run(([127, 0, 0, 1], 3030)).await;
}
