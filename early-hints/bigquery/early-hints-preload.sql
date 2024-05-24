-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2024-01-11
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/96816
-- Repository: https://github.com/mb/scripts

-- This query extracts and caches all telemetry data for the experiment in an
-- intermediate table for further analysis.

DECLARE start_date DATE DEFAULT DATE("2023-12-18");
DECLARE end_date DATE DEFAULT DATE("2024-01-10");
DECLARE channel STRING DEFAULT "release";
DECLARE experiment STRING DEFAULT "early-hints-preload";

WITH histogram AS (
    SELECT
        client_id,
        FORMAT_TIMESTAMP("%Y-%m-%d", submission_timestamp) as submission_date,
        mozfun.map.get_key(environment.experiments, experiment).branch AS experiment_branch,
        RTRIM(prestar, '_') AS server_response,
        mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_PAGE_LOAD_TIME_MS, prestar) AS page_load_time,
        mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_FIRST_CONTENTFUL_PAINT_MS, prestar) AS first_contentful_paint
    FROM telemetry.main, UNNEST(['preload_0', "preload_1"]) prestar
    WHERE DATE(submission_timestamp) >= start_date
        AND DATE(submission_timestamp) <= end_date
        AND normalized_channel = channel
        AND STARTS_WITH(application.display_version, "121")
        AND normalized_app_name = "Firefox"
        AND payload.processes.parent.scalars.browser_engagement_total_uri_count > 0
        AND mozfun.map.get_key(environment.experiments, experiment).branch IS NOT NULL
        AND (mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_PAGE_LOAD_TIME_MS, prestar) IS NOT NULL
          OR mozfun.map.get_key(payload.processes.content.keyed_histograms.EH_PERF_FIRST_CONTENTFUL_PAINT_MS, prestar) IS NOT NULL)
), plt_merged AS (
    SELECT
        client_id,
        submission_date,
        experiment_branch,
        server_response,
        JSON_QUERY(page_load_time, "$.values") as page_load_time,
    FROM histogram
), fcp_merged AS (
    SELECT
        client_id,
        submission_date,
        experiment_branch,
        server_response,
        JSON_QUERY(first_contentful_paint, "$.values") as first_contentful_paint
    FROM histogram
)
SELECT
        fcp_merged.client_id,
        fcp_merged.submission_date,
        fcp_merged.experiment_branch,
        fcp_merged.server_response,
        page_load_time,
        first_contentful_paint
FROM fcp_merged FULL JOIN plt_merged
    ON fcp_merged.client_id = plt_merged.client_id
        AND fcp_merged.submission_date = plt_merged.submission_date
        AND fcp_merged.experiment_branch = plt_merged.experiment_branch
        AND fcp_merged.server_response = plt_merged.server_response
