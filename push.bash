#!/bin/bash

API_KEY=$(cat ~/.config/sql-mozilla-api-key)

while read -r IN_FILE QUERY_ID
do
	echo $IN_FILE
	jq -n --compact-output --monochrome-output --arg multiline "$(cat "$IN_FILE")" '{"query": $multiline}' | curl -X POST --data-binary @- "https://sql.telemetry.mozilla.org/api/queries/$QUERY_ID?api_key=$API_KEY"
done < query_list.tsv
