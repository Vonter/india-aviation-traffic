#!/bin/bash

# Initialize directory
mkdir -p "urls"

# Parent List
curl "https://www.dgca.gov.in/digigov-portal/scan?" -X POST  --data-raw "baseLocale=&screenId=10000001&classification=&actionVal=viewStaticData&requestType=ApplicationRH&attachId=&langType=&ruleBookId=259&contentId=4184&serviceName=getParentData&attr=" > list.json

# Carrier-wise list
cat list.json | grep -Po "jsp[[:alnum:]\/\s\_]*.[a-z]*" | sed 's/jsp\/dgca/https:\/\/public-prd-dgca.s3.ap-south-1.amazonaws.com/g' | sort | grep xls > "urls/carriers.txt"

# City-wise list
for contentid in $(cat list.json | grep -Po "monthlyStatistics.*?html" | cut -d '/' -f 3 | sort -u);
do
  sleep 3
  curl "https://www.dgca.gov.in/digigov-portal/scan?" -X POST  --data-raw "baseLocale=&screenId=10000001&classification=&actionVal=viewStaticData&requestType=ApplicationRH&attachId=&ruleBookId=259&contentId=${contentid}&serviceName=fetchRulebookContentDtlsList&attr=" > "urls/$contentid.json"
done
for file in $(ls "urls" | grep json); do cat "urls/${file}" | grep -Po "jsp[[:alnum:]\/\s\_\%\,]*.[a-z]*" | sed 's/jsp\/dgca/https:\/\/public-prd-dgca.s3.ap-south-1.amazonaws.com/g' | sort | grep xls; done | sort -u > "urls/cities.txt"

# International list
for table in {1..4};
do
  for year in {15..24};
  do
    for quarter in {1..4};
    do
      echo "https://public-prd-dgca.s3.ap-south-1.amazonaws.com/InventoryList/dataReports/aviationDataStatistics/airTransport/international/quaterly/${year}Q${quarter}_${table}.xlsx" >> "urls/international.txt"
    done
  done
done

# Merge
cat "urls/carriers.txt" "urls/cities.txt" "urls/international.txt" | sort -u > urls.txt

# Clear temporary files
rm list.json
rm -Rf urls
