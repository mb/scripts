-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2024-05-30
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/100097
-- Repository: https://github.com/mb/scripts

-- Whether purged bounce trackers are classified on tracking lists
-- Telemetry probe: https://dictionary.telemetry.mozilla.org/apps/firefox_desktop/metrics/bounce_tracking_protection_purge_count_classified_tracker

DECLARE end_date DATE DEFAULT DATE("{{ End Date }}"); -- CURRENT_DATE()
DECLARE graph_duration INT64 DEFAULT {{ Time Range }}; -- 90
DECLARE channel STRING DEFAULT "{{ channel }}"; -- "nightly", "beta", "release"

SELECT
    DATE(submission_timestamp) AS day,
    "classified" AS label,
    SUM(metrics.counter.bounce_tracking_protection_purge_count_classified_tracker) AS num_purges
FROM firefox_desktop.metrics AS m
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND normalized_channel = channel
    AND metrics.counter.bounce_tracking_protection_purge_count_classified_tracker IS NOT NULL
GROUP BY day

UNION ALL -- https://stackoverflow.com/a/76917101

SELECT
    DATE(submission_timestamp) AS day,
    bucket.key AS label,
    SUM(bucket.value) AS num_purges
FROM firefox_desktop.metrics AS m
    CROSS JOIN UNNEST(metrics.labeled_counter.bounce_tracking_protection_purge_count) AS bucket
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND normalized_channel = channel
    AND ARRAY_LENGTH(metrics.labeled_counter.bounce_tracking_protection_purge_count) != 0
GROUP BY day, label
