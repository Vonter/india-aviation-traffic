#!/bin/bash

IFS=$'\n';

mkdir -p "raw/xlsx/domestic"
mkdir -p "raw/xlsx/international"

for url in $(cat "urls.txt");
do

  filename=$(echo $url | rev | cut -d '/' -f 1 | rev)
  encoded_filename=$(echo $filename | sed 's/ /%20/g')

  if [[ "$url" == *"domestic"* ]]; then
    if ! [ -f "raw/xlsx/domestic/${filename}" ]; then
      curl "https://public-prd-dgca.s3.ap-south-1.amazonaws.com/InventoryList/dataReports/aviationDataStatistics/airTransport/domestic/monthly/${encoded_filename}" > "raw/xlsx/domestic/${filename}"
      sleep 5
    fi
  else
    if ! [ -f "raw/xlsx/international/${filename}" ]; then
      curl "https://public-prd-dgca.s3.ap-south-1.amazonaws.com/InventoryList/dataReports/aviationDataStatistics/airTransport/international/quaterly/${encoded_filename}" > "raw/xlsx/international/${filename}"
      sleep 5
    fi
  fi

done
