-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-08-31
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/94302
-- Repository: https://github.com/mb/one-time-scripts

-- Parameters:
--  * table:
--    * cached_query_94297 (2nd experiment) or
--    * cached_query_94296 (1st experiment)

SELECT experiment_branch, RTRIM(server_response, "-01") AS server_responses, COUNT(DISTINCT client_id) AS count
FROM {{table}}
GROUP BY experiment_branch, server_responses
