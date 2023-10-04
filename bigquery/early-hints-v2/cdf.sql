-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-09-07
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/94451
-- Repository: https://github.com/mb/scripts

-- Generates function values for the probability density function [PDF]
-- and cumulative distribution function [CDF]. Also interesting, but
-- possible only with advanced tooling would be to display kernel density
-- estimation [KDE] for the PDF and the empirical cumulative distribution
-- function [eCDF] for the CDF.
--
-- [PDF]: https://en.wikipedia.org/w/index.php?title=Probability_density_function&oldid=1172411601
-- [CDF]: https://en.wikipedia.org/w/index.php?title=Cumulative_distribution_function&oldid=1161135407
-- [KDE]: https://en.wikipedia.org/w/index.php?title=Kernel_density_estimation&oldid=1169216425
-- [eCDF]: https://en.wikipedia.org/w/index.php?title=Empirical_distribution_function&oldid=1170611115
--
-- Parameters:
--  * table:
--    * cached_query_94671 (3rd experiment) or
--    * cached_query_94297 (2nd experiment) or
--    * cached_query_94296 (1st experiment)
--  * server_response:
--    * "preconnect"
--    * "preload%"
--    * "preconnect-preload%"
--  * metric:
--    * page_load_time
--    * first_contentful_paint

WITH extract AS (
    -- going from '{"bucket_count":100,"histogram_type":0,"sum":1396,"range":[1,50000],"values":{"1183":0,"1302":1,"1433":0}}'
    -- to '{"1183":0,"1302":1,"1433":0}}'
    SELECT
        experiment_branch,
        client_id,
        server_response,
        json_extract({{metric}}, "$.values") as vs
    FROM {{table}}
    WHERE server_response LIKE {{server_response}}
), extracted AS (
    -- buckets to columns
    SELECT experiment_branch, client_id, CAST(j.key AS INTEGER) as ms, j.value as c
    FROM extract t, json_each(vs) j
    WHERE c != 0
), by_users AS (
    -- accumulate each histogram bucket per user
    SELECT experiment_branch, client_id, ms, SUM(c) as s
    FROM extracted
    GROUP BY experiment_branch, client_id, ms
), total_by_users AS (
    -- calculate total amount of requests per user
    SELECT experiment_branch, client_id, SUM(c) as total
    FROM extracted
    GROUP BY experiment_branch, client_id
), normalize AS (
    -- normalize each user histogram
    -- '*1.0' to convert to float, s: sum, c: normalized sum
    SELECT experiment_branch, client_id, ms, s*1.0 as s, (s*1.0 / total) as c
    FROM by_users NATURAL JOIN total_by_users
), pdf AS (
    -- accumulate each bucket
    SELECT
        experiment_branch,
        ms,
        SUM(s) AS by_clients,
        SUM(c) AS normalized_by_client
    FROM normalize
    GROUP BY experiment_branch, ms
)

-- calculate cdf from pdf
SELECT
    experiment_branch,
    ms,
    by_clients,
    SUM(by_clients) OVER (PARTITION BY experiment_branch ORDER BY ms) / SUM(by_clients) OVER (PARTITION BY experiment_branch) AS by_client_cdf,
    normalized_by_client,
    SUM(normalized_by_client) OVER (PARTITION BY experiment_branch ORDER BY ms) / SUM(normalized_by_client) OVER (PARTITION BY experiment_branch) AS normalized_by_client_cdf
FROM pdf
