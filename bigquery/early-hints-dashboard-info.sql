-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-09-19
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/94674
-- Repository: https://github.com/mb/scripts

-- show experiment info in dashboard

WITH temp_data AS (
    SELECT 
        'cached_query_94671' AS cached_table,
        'early-hints-preconnect' AS name,
        '2023-09-18' AS experiment_start,
        'TBD' AS enrolment_end,
        'TBD' AS experiment_end
    UNION ALL
    SELECT
        'cached_query_94297'AS cached_table,
        'early-hints-performance-v2' AS name,
        '2023-06-14' AS experiment_start,
        '2023-06-21' AS enrolment_end,
        '2023-07-05' AS experiment_end
    UNION ALL
    SELECT
        'cached_query_94296' AS cached_table,
        'early-hints-performance' AS name,
        '2023-05-16' AS experiment_start,
        '2023-06-25' AS enrolment_end,
        '2023-06-08' AS experiment_end
)

SELECT
    name, experiment_start, enrolment_end, experiment_end
FROM temp_data
WHERE cached_table = "{{table}}";
