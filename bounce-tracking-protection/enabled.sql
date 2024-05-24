-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2024-05-22
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/100094
-- Repository: https://github.com/mb/scripts

-- This query extract usage information on bouncetrackingprotection
-- The following telemetry is aggregated:
-- * https://dictionary.telemetry.mozilla.org/apps/firefox_desktop/metrics/bounce_tracking_protection_enabled_at_startup
-- * https://dictionary.telemetry.mozilla.org/apps/firefox_desktop/metrics/bounce_tracking_protection_enabled_dry_run_mode_at_startup

DECLARE end_date DATE DEFAULT DATE("{{ End Date }}"); -- CURRENT_DATE()
DECLARE graph_duration INT64 DEFAULT {{ Time Range }}; -- 90
DECLARE channel STRING DEFAULT "{{ channel }}"; -- "nightly", "beta", "stable"

SELECT
    DATE(submission_timestamp) AS day,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_at_startup = true) AS enabled,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_at_startup = false) AS disabled,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_dry_run_mode_at_startup = true) AS dry,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_dry_run_mode_at_startup = false) AS not_dry,
FROM firefox_desktop.metrics AS m
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND metrics.boolean.bounce_tracking_protection_enabled_at_startup IS NOT NULL
    AND normalized_channel = channel
GROUP BY
    day
