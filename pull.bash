#!/bin/bash

API_KEY=$(cat ~/.config/sql-mozilla-api-key)

while read -r OUT_FILE QUERY_ID
do
	curl "https://sql.telemetry.mozilla.org/api/queries/$QUERY_ID?api_key=$API_KEY" | jq .query --raw-output > $OUT_FILE
done < query_list.tsv
