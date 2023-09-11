-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-09-11
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/92826
-- Repository: https://github.com/mb/one-time-scripts

DECLARE end_date DATE DEFAULT CURRENT_DATE;
DECLARE start_date DATE DEFAULT DATE_SUB(end_date, INTERVAL 14 DAY);
DECLARE sample INT64 DEFAULT 100;

SET end_date = CASE BYTE_LENGTH({{ End Date }})
WHEN 0 THEN CURRENT_DATE
ELSE CAST({{ End Date }} AS DATE) 
END;

SET start_date = CASE BYTE_LENGTH({{ Start Date }})
WHEN 0 THEN start_date
ELSE CAST({{ Start Date }} AS DATE) 
END;

WITH per_build_client_day AS (
    SELECT
        client_id,
        CONCAT(mozfun.map.get_key(environment.experiments, "early-hints-performance-v2").branch, '_', RTRIM(prestar, '01_')) AS branch,
        mozfun.hist.merge(
            ARRAY_AGG(
                mozfun.hist.extract(
                    mozfun.map.get_key(payload.processes.content.keyed_histograms.{{keyedprobe}}, prestar)
                ) IGNORE NULLS
            )
        ) AS extracted
    FROM
        {{db}},
        UNNEST(['preconnect_', 'preload_0', 'preload_1', 'preconnect_preload_0', 'preconnect_preload_1']) prestar
    WHERE
        DATE(submission_timestamp) >= start_date
        AND DATE(submission_timestamp) <= end_date
        AND normalized_channel = {{ channel }}
        AND normalized_app_name = "Firefox"
        AND SAFE.PARSE_DATE('%F',SUBSTR(payload.info.subsession_start_date, 0, 10)) IS NOT NULL
        AND payload.processes.parent.scalars.browser_engagement_total_uri_count > 0
        AND mozfun.map.get_key(environment.experiments, "early-hints-performance-v2").branch IS NOT NULL
    GROUP BY
        client_id, branch
),

merged_histograms AS (
    SELECT
        client_id,
        branch,
        KEY as LoadTime,
        SUM(value) AS value,
    FROM
        per_build_client_day
    CROSS JOIN
        UNNEST(per_build_client_day.extracted.VALUES)
    GROUP BY
        client_id, branch, LoadTime
),

as_struct AS (
    SELECT
        branch,
        client_id,
        LoadTime,
    FROM merged_histograms,
    UNNEST(GENERATE_ARRAY(1, value))
)

, summary AS (
    SELECT
        branch,
        LoadTime,
        COUNT(client_id) AS n,
    FROM as_struct
    GROUP BY branch, LoadTime
    ORDER BY LoadTime
)

SELECT
    branch,
    LoadTime,
    SUM(n) OVER (PARTITION BY branch ORDER BY LoadTime) / SUM(n) OVER (PARTITION BY branch) AS cdf,
FROM summary
