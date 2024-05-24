#!/bin/bash

API_KEY=$(cat ~/.config/sql-mozilla-api-key)

while read -r OUT_FILE QUERY_ID
do
	# https://superuser.com/a/186304
	if [ "$#" -eq 0 ] || [[ "$*" == *"$QUERY_ID"* ]]; then
		curl "https://sql.telemetry.mozilla.org/api/queries/$QUERY_ID?api_key=$API_KEY" | jq .query --raw-output > $OUT_FILE
	fi
done < query_list.tsv
