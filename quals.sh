#!/bin/bash
#jq -r '.[].events.[] | [.event_key, .name, .event_type, .qual_record.wins, .qual_record.losses, .qual_record.ties] | join(",")' frc3620_history.json 
jq -r '.[].events.[] | [.event_key, .short_name, .event_type, .qual_status, .qual_record.wins, .qual_record.losses, .qual_record.ties, .alliance_status, .playoff_record.wins, .playoff_record.losses, .playoff_record.ties, .playoff_status] | join(",")' $1 
