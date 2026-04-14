#!/bin/bash
jq -r '.[].events.[] | [.event_key, .short_name, .event_type, ([.awards[]] | join(";"))] | join(",")' $1
