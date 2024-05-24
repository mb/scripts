#!/bin/bash

rg 'BigQuery Link:' | sed 's|queries/|:|' | awk -F':' '{print $1 "\t" $NF }' | rg --invert-match 'template.sql' | sort > query_list.tsv
