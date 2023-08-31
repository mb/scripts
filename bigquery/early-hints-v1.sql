-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-08-31
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/94296
-- Repository: https://github.com/mb/one-time-scripts

-- This query extracts and caches all telemetry data for the experiment in an
-- intermediate table for further analysis.

DECLARE start_date DATE DEFAULT DATE("2023-05-10");
DECLARE end_date DATE DEFAULT DATE("2023-06-10");
DECLARE in_version STRING DEFAULT "114.0b";
DECLARE channel STRING DEFAULT "beta";
DECLARE experiment STRING DEFAULT "early-hints-performance";

SELECT
    client_id,
    SAFE.PARSE_DATE('%F', SUBSTR(payload.info.subsession_start_date, 0, 10)) AS submission_date,
    REPLACE(REPLACE(
        mozfun.map.get_key(environment.experiments, experiment).branch,
        'treatment-a', 'eh-enabled'),
        'control', 'eh-disabled'
    ) AS experiment_branch,
    REPLACE(RTRIM(prestar, '_'), '_', '-') AS server_response,
    mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_PAGE_LOAD_TIME_MS, prestar) AS page_load_time,
    mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_FIRST_CONTENTFUL_PAINT_MS, prestar) AS first_contentful_paint
FROM telemetry.main, UNNEST(['preconnect_', 'preload_0', 'preload_1', 'preconnect_preload_0', 'preconnect_preload_1']) prestar
WHERE DATE(submission_timestamp) >= start_date
    AND DATE(submission_timestamp) <= end_date
    AND normalized_channel = channel
    AND STARTS_WITH(application.display_version, in_version)
    AND normalized_app_name = "Firefox"
    AND SAFE.PARSE_DATE('%F', SUBSTR(payload.info.subsession_start_date, 0, 10)) IS NOT NULL
    AND payload.processes.parent.scalars.browser_engagement_total_uri_count > 0
    AND mozfun.map.get_key(environment.experiments, experiment).branch IS NOT NULL
    AND (mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_PAGE_LOAD_TIME_MS, prestar) IS NOT NULL
      OR mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_FIRST_CONTENTFUL_PAINT_MS, prestar) IS NOT NULL)
