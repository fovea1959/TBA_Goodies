#!/bin/bash
jq -r '.[] | [.year, .district_ranking, .district_size, .district_percentile] | join(",")' frc3620_history.json 
