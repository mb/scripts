-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-08-31
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/93053
-- Repository: https://github.com/mb/one-time-scripts

-- This script was used to extract the telemetry data and later publish it on
-- the necko blog: https://mozilla-necko.github.io
-- Bug: https://bugzilla.mozilla.org/show_bug.cgi?id=1841626
-- Together with the python script `preprocess.py`

-- parameters:
--  * experiment: "early-hints-performance", "early-hints-performance-v2"
--  * db: telementry.main, telemetry.main_1pct

DECLARE end_date DATE DEFAULT CURRENT_DATE;
DECLARE start_date DATE DEFAULT DATE_SUB(end_date, INTERVAL 14 DAY);
DECLARE in_version STRING DEFAULT "114.0b";
DECLARE channel STRING DEFAULT "beta";

SET start_date = CASE {{experiment}}
    WHEN "early-hints-performance" THEN DATE("2023-05-10")
    WHEN "early-hints-performance-v2" THEN DATE("2023-06-10")
    ELSE start_date
END;

SET end_date = CASE {{experiment}}
    WHEN "early-hints-performance" THEN DATE("2023-06-10")
    WHEN "early-hints-performance-v2" THEN DATE("2023-07-10")
    ELSE end_date
END;

SET in_version = CASE {{experiment}}
    WHEN "early-hints-performance" THEN "114.0b"
    WHEN "early-hints-performance-v2" THEN "115.0b"
    ELSE in_version
END;

SELECT
    client_id,
    SAFE.PARSE_DATE('%F',SUBSTR(payload.info.subsession_start_date, 0, 10)) as submission_date,
    mozfun.map.get_key(environment.experiments, {{experiment}}).branch as experiment_branch,
    RTRIM(prestar, '_') AS server_response,
    mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_PAGE_LOAD_TIME_MS, prestar) as page_load_time,
    mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_FIRST_CONTENTFUL_PAINT_MS, prestar) as first_contentful_paint
FROM
    {{db}},
    UNNEST(['preconnect_', 'preload_0', 'preload_1', 'preconnect_preload_0', 'preconnect_preload_1']) prestar
WHERE
    DATE(submission_timestamp) >= start_date
    AND DATE(submission_timestamp) <= end_date
    AND normalized_channel = channel
    AND STARTS_WITH(application.display_version, in_version)
    AND normalized_app_name = "Firefox"
    AND SAFE.PARSE_DATE('%F',SUBSTR(payload.info.subsession_start_date, 0, 10)) IS NOT NULL
    AND payload.processes.parent.scalars.browser_engagement_total_uri_count > 0
    AND mozfun.map.get_key(environment.experiments, {{experiment}}).branch IS NOT NULL
    AND (
        mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_PAGE_LOAD_TIME_MS, prestar) IS NOT NULL
        OR mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_FIRST_CONTENTFUL_PAINT_MS, prestar) IS NOT NULL
    )
