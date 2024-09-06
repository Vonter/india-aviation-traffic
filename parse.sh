#!/bin/bash

IFS=$'\n';

mkdir -p "raw/csv/domestic"
mkdir -p "raw/csv/international"

# Find .xls and .xlsx files recursively
find "raw/xlsx" \( -iname "*.xls" -o -iname "*.xlsx" \) -print0 | while IFS= read -r -d '' file; do

  # Extract filename without extension for output file naming
  filename=$(basename -- "$file")
  filename="${filename%.*}"
  
  # Define output CSV file name
  output_file=${file//xlsx/csv}
  output_file=${output_file//xls/csv}

  # Run ssconvert on the .xls or .xlsx file
  ssconvert "$file" "${output_file}"

done
