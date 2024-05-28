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

WITH agg_info AS (
SELECT
    DATE(submission_timestamp) AS day,
    COUNT(DISTINCT client_info.client_id) AS num_users,
    SUM(bucket.value) AS num_purges
FROM firefox_desktop.metrics AS m
    CROSS JOIN UNNEST(metrics.timing_distribution.bounce_tracking_protection_purge_duration.values) AS bucket
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND metrics.timing_distribution.bounce_tracking_protection_purge_duration IS NOT NULL
    AND normalized_channel = channel
    AND bucket.value > 0
GROUP BY day
), total_enabled AS (
SELECT
    DATE(submission_timestamp) AS day,
    COUNT(DISTINCT client_info.client_id) AS enabled,
FROM firefox_desktop.metrics AS m
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND metrics.boolean.bounce_tracking_protection_enabled_at_startup IS NOT NULL
    AND normalized_channel = channel
    AND metrics.boolean.bounce_tracking_protection_enabled_at_startup = true
    AND metrics.boolean.bounce_tracking_protection_enabled_dry_run_mode_at_startup = false
GROUP BY day
)
SELECT
    agg_info.day,
    total_enabled.enabled AS num_users,
    num_users AS num_users_with_at_least_one_purge,
    num_purges,
    (num_purges/num_users) AS purges_per_user_with_at_least_one_purge, -- purges per user with at least one purge
    (num_purges/total_enabled.enabled) AS purges_per_user -- this might include users that don't really use their browser
FROM
    agg_info JOIN total_enabled
    ON agg_info.day = total_enabled.day

