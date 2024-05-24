-- This Source Code Form is subject to the terms of the Mozilla Public
-- License, v. 2.0. If a copy of the MPL was not distributed with this
-- file, You can obtain one at https://mozilla.org/MPL/2.0/.

-- Author: Manuel Bucher <dev@manuelbucher.com>
-- Date: 2023-09-07
-- Repository: https://github.com/mb/scripts

-- Example on how to extract histogram data in sqlite
-- Result:
--
-- key  | value
-- ---- | -----
-- 2316 | 0
-- 2549 | 1
-- 2806 | 0


WITH tablename AS (
  SELECT '{"2316":0,"2549":1,"2806":0}' AS col
)

SELECT j.key, j.value
FROM tablename t, json_each(t.col) j;
