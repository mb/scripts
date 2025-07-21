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
use indoc::formatdoc;
use serde::Deserialize;
use text_to_png::TextRenderer;
use url::Url;
use uuid::Uuid;
use warp::{
    Filter,
    filters::path::Tail,
    http::{HeaderValue, StatusCode},
    hyper::Body,
    reply::{self, Reply, Response},
};

#[derive(Deserialize)]
struct Query {
    id: Option<Uuid>,
    target: Option<Url>,
}

struct Request {
    host: Option<String>,
    query: Query,
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
        let wiki = "#dfeeff";
        let cx = "#acab9d";
        let neon = "#ffc3bc";

        let background_color = if let Some(host) = self.host.as_ref() {
            match host.as_str() {
                "sah.yet.wiki" => wiki,
                "sah.yet.cx" => cx,
                "sah.neon.rocks" => neon,
                _ => "ffffff",
            }
        } else {
            "ffffff"
        };
        formatdoc!(
            "
            <style>
                body {{
                    background-color: {background_color};
                }}
                .wiki {{ background-color: {wiki}; }}
                .cx {{ background-color: {cx}; }}
                .neon {{ background-color: {neon}; }}
                p {{
                    margin: 0;
                }}
                table {{
                    border-collapse: collapse;
                }}

                th, td {{
                    padding: 0px;
                    border: 1px solid #000;
                    vertical-align: baseline;
                }}
            </style>"
        )
    }
    // simulate SSO auth flow with user interaction
    fn auth(&self) -> Response {
        let target = self
            .query
            .target
            .clone()
            .unwrap_or(Url::parse("https://example.invalid").unwrap());

        let style = self.style();
        let response = formatdoc!(
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
                        <input type="submit" value="Submit" formaction="track/{target}">
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
    fn track(&self, leftover: Option<&str>) -> Response {
        let mut target = match (self.query.target.as_ref(), leftover) {
            (Some(target), _) => target.clone(),
            (_, Some(leftover)) => match Url::parse(leftover) {
                Ok(url) => url,
                Err(err) => {
                    return reply::with_status(
                        format!("Invalid target url given {err:?}"),
                        StatusCode::BAD_REQUEST,
                    )
                    .into_response();
                }
            },
            _ => {
                return reply::with_status(format!("No target url given"), StatusCode::BAD_REQUEST)
                    .into_response();
            }
        };

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
        let id = id.unwrap_or_else(Uuid::now_v7);
        target.query_pairs_mut().append_pair("id", &id.to_string());
        warp::http::Response::builder()
            .header("Location", target.as_str())
            .header("Set-Cookie", &format!("id={id}; Secure; HttpOnly"))
            .status(307)
            .body(Body::empty())
            .unwrap()
    }

    fn table(req: &str) -> String {
        formatdoc!(
            r#"
            <table>
                <thead>
                    <tr>
                        <th></td>
                        <th class="neon">neon.rocks</td>
                        <th class="wiki">yet.wiki</td>
                        <th class="cx">yet.cx</td>
                    </tr>
                </thead>
                <tr>
                    <td>host</td>
                    <td><span id="neon-{req}-host" class="neon host"></span></td>
                    <td><span id="wiki-{req}-host" class="wiki host"></span></td>
                    <td><span id="cx-{req}-host" class="cx host"></span></td>
                </tr>
                <tr>
                    <td>origin</td>
                    <td><span id="neon-{req}-origin" class="neon origin"></span></td>
                    <td><span id="wiki-{req}-origin" class="wiki origin"></span></td>
                    <td><span id="cx-{req}-origin" class="cx origin"></span></td>
                </tr>
                <tr>
                    <td>referer</td>
                    <td><span id="neon-{req}-referer" class="neon referer"></span></td>
                    <td><span id="wiki-{req}-referer" class="wiki referer"></span></td>
                    <td><span id="cx-{req}-referer" class="cx referer"></span></td>
                </tr>
                <tr>
                    <td>cookie</td>
                    <td><span id="neon-{req}-cookie" class="neon cookie"></span></td>
                    <td><span id="wiki-{req}-cookie" class="wiki cookie"></span></td>
                    <td><span id="cx-{req}-cookie" class="cx cookie"></span></td>
                </tr>
                <tr>
                    <td>sec-fetch-storage-access</td>
                    <td><span id="neon-{req}-sah" class="neon host"></span></td>
                    <td><span id="wiki-{req}-sah" class="wiki host"></span></td>
                    <td><span id="cx-{req}-sah" class="cx host"></span></td>
                </tr>
            </table>
            "#
        )
    }
}

impl Request {
    fn main(&self, url: &Url) -> Response {
        let style = self.style();
        let fetch = Request::table("fetch");
        let css = Request::table("css");
        let js = Request::table("js");
        let iframe_id = Uuid::new_v4();
        let target = url::form_urlencoded::Serializer::new(String::new())
            .append_pair("target", url.as_str())
            .finish();
        let response = formatdoc!(
            r#"
            <!DOCTYPE html>
            <html>
                <head><title>Storage-Access-API test ground</title></head>
                <body>
                    {style}
                    <h1>Storage-Access-API test ground</h1>
                    Url: {url}<br>
                    If a header doesn't exist, null will be displayed. If it has a value, an additional round of quotes (&quot;) will be displayed.<br>
                    Links to set unpartitioned storage on the third party domain:
                    <table>
                        <thead>
                            <tr>
                                <th class="neon">neon.rocks</td>
                                <th class="wiki">yet.wiki</td>
                                <th class="cx">yet.cx</td>
                            </tr>
                        </thead>
                        <tr>
                            <td class="neon"><a href="https://sah.neon.rocks/storage-access/">index</a></td>
                            <td class="wiki"><a href="https://sah.yet.wiki/storage-access/">index</a></td>
                            <td class="cx"><a href="https://sah.yet.cx/storage-access/">index</a></td>
                        </tr>
                        <tr>
                            <td class="neon"><a href="https://sah.neon.rocks/storage-access/auth?{target}">auth</a></td>
                            <td class="wiki"><a href="https://sah.yet.wiki/storage-access/auth?{target}">auth</a></td>
                            <td class="cx"><a href="https://sah.yet.cx/storage-access/auth?{target}">auth</a></td>
                        </tr>
                        <tr>
                            <td class="neon"><a href="https://sah.neon.rocks/storage-access/track?{target}">track</a></td>
                            <td class="wiki"><a href="https://sah.yet.wiki/storage-access/track?{target}">track</a></td>
                            <td class="cx"><a href="https://sah.yet.cx/storage-access/track?{target}">track</a></td>
                        </tr>
                    </table>
                    <h2>Main document headers</h2>
                    <p>Host: <span class="cookie">{host}</span></p>
                    <p>Origin: <span class="origin">{origin}</span></p>
                    <p>Referer: <span class="referer">{referer}</span></p>
                    <p>Cookie: <span class="cookie">{cookie}</span></p>
                    <p>Sec-Fetch-Storage-Access: <span class="sah">{sec_fetch_storage_access}</span></p>
                    <h2>Fetch headers <a href="https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#including_credentials">with credentials</a><small>(<a href="/storage-access/fetch.json">/storage-access/fetch.json</a>)</small></h2>
                    {fetch}
                    <script>
                        let headers = ["host", "origin", "referer", "cookie", "sah"];
                        let sites = {{
                            neon: "https://sah.neon.rocks/storage-access/fetch.json",
                            wiki: "https://sah.yet.wiki/storage-access/fetch.json",
                            cx: "https://sah.yet.cx/storage-access/fetch.json",
                        }}
                        for (const [key, site] of Object.entries(sites)) {{
                            fetch(site, {{ credentials: "include" }})
                                .then((response) => response.json())
                                .then((response) => {{
                                    for (const header in headers) {{
                                        document.getElementById(key+"-fetch-"+headers[header]).innerText = response[headers[header]];
                                    }}
                                }});
                        }}
                    </script>
                    <h2>CSS headers <small>(<a href="/storage-access/style.css">/storage-access/style.css</a>)</small></h2>
                    {css}
                    <link href="https://sah.neon.rocks/storage-access/style.css" rel="stylesheet" />
                    <link href="https://sah.yet.wiki/storage-access/style.css" rel="stylesheet" />
                    <link href="https://sah.yet.cx/storage-access/style.css" rel="stylesheet" />
                    <h2>Script headers <small>(<a href="/storage-access/script.js">/storage-access/script.js</a>)</small></h2>
                    {js}
                    <script src="https://sah.neon.rocks/storage-access/script.js"></script>
                    <script src="https://sah.yet.wiki/storage-access/script.js"></script>
                    <script src="https://sah.yet.cx/storage-access/script.js"></script>
                    <h2>Image headers <small>(<a href="/storage-access/image.png">/storage-access/image.png</a>)</small></h2>
                    <p><img src="https://sah.neon.rocks/storage-access/image.png" /></p>
                    <p><img src="https://sah.yet.wiki/storage-access/image.png" /></p>
                    <p><img src="https://sah.yet.cx/storage-access/image.png" /></p>
                    <h2>Iframe headers</h2>
                    <table>
                        <thead>
                            <tr>
                                <th class="neon">neon.rocks</td>
                                <th class="wiki">yet.wiki</td>
                                <th class="cx">yet.cx</td>
                            </tr>
                        </thead>
                        <tr>
                            <td class="neon"><a href="https://sah.neon.rocks/storage-access/iframe.html" target="{iframe_id}">iframe</a></td>
                            <td class="wiki"><a href="https://sah.yet.wiki/storage-access/iframe.html" target="{iframe_id}">iframe</a></td>
                            <td class="cx"><a href="https://sah.yet.cx/storage-access/iframe.html" target="{iframe_id}">iframe</a></td>
                        </tr>
                    </table>
                    <iframe name="{iframe_id}" src="about:blank" width="100%" height="2000"></iframe>
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
        let response = formatdoc!(
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
        let response = formatdoc!(
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
        let response = formatdoc!(
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
                let headers = response.headers_mut();
                headers.append("access-control-allow-origin", host);
                headers.append(
                    "access-control-allow-credentials",
                    HeaderValue::from_static("true"),
                );
            }
        }
        response
    }

    fn png(&self) -> Response {
        // TODO: multiline text with imageproc?
        // https://github.com/RookAndPawn/text-to-png/issues/3
        let response = formatdoc!(
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

    pub fn respond(&self, endpoint: Tail) -> Response {
        let host = self.host.as_ref().unwrap();
        let url = format!("https://{host}/storage-access/{}", endpoint.as_str());
        let url = Url::parse(&url).unwrap();
        let (endpoint, leftover) =
            if let Some((endpoint, data)) = endpoint.as_str().split_once(|c| c == '/') {
                (endpoint, Some(data))
            } else {
                // no further data in url
                (endpoint.as_str(), None)
            };

        match endpoint {
            // information
            "" | "iframe.html" => self.main(&url),
            "style.css" => self.css(),
            "script.js" => self.js(),
            "fetch.json" => self.json(),
            "image.png" => self.png(),
            // track
            "auth" => self.auth(),
            "track" => self.track(leftover),
            _ => reply::with_status(format!("Not found! {url}"), StatusCode::NOT_FOUND)
                .into_response(),
        }
    }
}

#[tokio::main]
async fn main() {
    let sah = warp::path("storage-access")
        .and(warp::path::tail())
        .and(warp::query::query())
        .and(warp::header::optional("host"))
        .and(warp::header::optional("origin"))
        .and(warp::header::optional("referer"))
        .and(warp::header::optional("cookie"))
        // storage-access-header request
        .and(warp::header::optional("sec-fetch-storage-access"))
        .map(
            |endpoint, query, host, origin, referer, cookie, sec_fetch_storage_access| {
                Request {
                    host,
                    query,
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
