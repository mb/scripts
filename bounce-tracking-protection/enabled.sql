-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2024-05-22
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/100094
-- Repository: https://github.com/mb/scripts

-- This query extract usage information on bouncetrackingprotection

DECLARE end_date DATE DEFAULT CURRENT_DATE();
DECLARE graph_duration INT64 DEFAULT 90;
DECLARE channel STRING DEFAULT "nightly";

SELECT
    DATE(submission_timestamp) AS day,
    client_info.app_display_version AS fx_version
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_at_startup = true) AS enabled,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_at_startup = false) AS not_enabled,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_dry_run_mode_at_startup = true) AS dry,
    COUNTIF(metrics.boolean.bounce_tracking_protection_enabled_dry_run_mode_at_startup = false) AS not_dry,
FROM firefox_desktop.metrics AS m
WHERE
    DATE(submission_timestamp) > DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND end_date > DATE(submission_timestamp)
    AND metrics.boolean.bounce_tracking_protection_enabled_at_startup IS NOT NULL
    AND normalized_channel = channel
GROUP BY
    day, fx_version
