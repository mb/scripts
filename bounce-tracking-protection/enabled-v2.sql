-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0.

-- Author: Paul Zuhlcke, Manuel Bucher
-- Date: 2024-11-12
-- BigQuery Link: https://sql.telemetry.mozilla.org/queries/100098
-- Repository: https://github.com/mb/scripts
-- Adapted to include channel filtering and ensure all variables are used.

DECLARE end_date DATE DEFAULT DATE("{{ End Date }}"); -- e.g., CURRENT_DATE()
DECLARE graph_duration INT64 DEFAULT {{ Time Range }}; -- e.g., 90
DECLARE channel STRING DEFAULT '{{ channel }}'; -- 'nightly', 'beta', 'release', or 'all' for all channels

SELECT
    DATE(submission_timestamp) AS day,
    CASE metrics.quantity.bounce_tracking_protection_mode
        WHEN 0 THEN 'MODE_DISABLED'
        WHEN 1 THEN 'MODE_ENABLED'
        WHEN 2 THEN 'MODE_ENABLED_STANDBY'
        WHEN 3 THEN 'MODE_ENABLED_DRY_RUN'
        ELSE 'UNKNOWN'
    END AS mode_label,
    COUNT(*) AS count
FROM
    `mozdata.firefox_desktop.metrics` AS m
WHERE
    DATE(submission_timestamp) >= DATE_SUB(end_date, INTERVAL graph_duration DAY)
    AND DATE(submission_timestamp) < end_date
    AND metrics.quantity.bounce_tracking_protection_mode IS NOT NULL
    AND (channel = 'all' OR m.normalized_channel = channel)
GROUP BY
    day,
    mode_label
ORDER BY
    day ASC,
    mode_label ASC

