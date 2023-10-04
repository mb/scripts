-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-09-07
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/94315
-- Repository: https://github.com/mb/scripts

WITH extract  AS (
    -- going from '{"bucket_count":100,"histogram_type":0,"sum":1396,"range":[1,50000],"values":{"1183":0,"1302":1,"1433":0}}'
    -- to '{"1183":0,"1302":1,"1433":0}}'
    SELECT
        client_id,
        json_extract(first_contentful_paint, "$.values") as fcp,
        json_extract(page_load_time, "$.values") as plt
    FROM {{table}}
)

SELECT SUM(j.value) as count
FROM extract t, json_each(t.plt) j;
