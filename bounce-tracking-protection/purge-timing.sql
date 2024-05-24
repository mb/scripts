-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2024-05-24
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/100095
-- Repository: https://github.com/mb/scripts

-- Purge timing distribution
-- The following telemetry is aggregated:
-- * https://dictionary.telemetry.mozilla.org/apps/firefox_desktop/metrics/bounce_tracking_protection_purge_duration

DECLARE end_date DATE DEFAULT DATE("{{ End Date }}"); -- CURRENT_DATE()
DECLARE graph_duration INT64 DEFAULT {{ Time Range }}; -- 90
DECLARE channel STRING DEFAULT "{{ channel }}"; -- "nightly", "beta", "stable"

SELECT
    DATE(submission_timestamp) AS day,
    metrics.timing_distribution.bounce_tracking_protection_purge_duration
FROM firefox_desktop.metrics AS m
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND metrics.timing_distribution.bounce_tracking_protection_purge_duration IS NOT NULL
    AND normalized_channel = channel
LIMIT 2
