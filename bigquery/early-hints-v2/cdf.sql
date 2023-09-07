-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-09-07
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/94315
-- Repository: https://github.com/mb/one-time-scripts

WITH extract AS (
    -- going from '{"bucket_count":100,"histogram_type":0,"sum":1396,"range":[1,50000],"values":{"1183":0,"1302":1,"1433":0}}'
    -- to '{"1183":0,"1302":1,"1433":0}}'
    SELECT
        experiment_branch,
        client_id,
        server_response,
        json_extract(first_contentful_paint, "$.values") as vs
    FROM {{table}}
    WHERE server_response LIKE {{server_response}}
), extracted AS (
    SELECT experiment_branch, client_id, CAST(j.key AS INTEGER) as ms, j.value as c
    FROM extract t, json_each(vs) j
    WHERE c != 0
), by_users AS (
    SELECT experiment_branch, client_id, ms, SUM(c) as s
    FROM extracted
    GROUP BY experiment_branch, client_id, ms
), total_by_users AS (
    SELECT experiment_branch, client_id, SUM(c) as total
    FROM extracted
    GROUP BY experiment_branch, client_id
), normalize AS (
    -- '*1.0' to convert to float
    SELECT experiment_branch, client_id, ms, s*1.0 as s, (s*1.0 / total) as c
    FROM by_users NATURAL JOIN total_by_users
)

-- calculate cdf
SELECT
    experiment_branch,
    ms,
    SUM(s) AS by_clients,
    SUM(s) OVER (PARTITION BY experiment_branch ORDER BY ms) / SUM(s) OVER (PARTITION BY experiment_branch) AS by_client_cdf,
    SUM(c) AS normalized_by_client,
    SUM(c) OVER (PARTITION BY experiment_branch ORDER BY ms) / SUM(c) OVER (PARTITION BY experiment_branch) AS normalized_by_client_cdf
FROM normalize
GROUP BY experiment_branch, ms
