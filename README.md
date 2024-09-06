# india-aviation-traffic

Dataset of Indian aviation traffic, by carrier and city. Sourced from [DGCA](https://www.dgca.gov.in/).

Browse the dataset using the below links:
- Domestic City-wise: <https://flatgithub.com/Vonter/india-aviation-traffic?filename=aggregated/domestic/city.csv&stickyColumnName=City1>
- International City-wise: <https://flatgithub.com/Vonter/india-aviation-traffic?filename=aggregated/international/city.csv&stickyColumnName=City1>
- International Country-wise: <https://flatgithub.com/Vonter/india-aviation-traffic?filename=aggregated/international/country.csv&stickyColumnName=Country>
- International Carrier-wise: <https://flatgithub.com/Vonter/india-aviation-traffic?filename=aggregated/international/carrier.csv&stickyColumnName=Airline>

## Dataset

The complete dataset is available as CSV files under the [csv/](csv) folder in this repository. The CSV files include details on passenger, freight and mail traffic depending on availability of data in a particular timeframe:
- [Domestic City-wise](aggregated/domestic/city.csv?raw=1)
- [International City-wise](aggregated/international/city.csv?raw=1)
- [International Country-wise](aggregated/international/country.csv?raw=1)
- [International Carrier-wise](aggregated/international/carrier.csv?raw=1)

## Scripts

- [initialize.sh](initialize.sh): Initializes the list of XLSX URLs to be fetched
- [fetch.sh](fetch.sh): Fetches the raw XLSX files from [DGCA](https://www.dgca.gov.in/)
- [parse.sh](parse.sh): Parses the raw XLSX files, and save them as equivalent CSV files
- [aggregate.py](aggregate.py): Parses the individual CSV files, and aggregates them into combined CSV files

## License

This india-aviation-traffic dataset is made available under the Open Database License: http://opendatacommons.org/licenses/odbl/1.0/. 
Users of this data should attribute DGCA: https://www.dgca.gov.in/digigov-portal/

You are free:

* **To share**: To copy, distribute and use the database.
* **To create**: To produce works from the database.
* **To adapt**: To modify, transform and build upon the database.

As long as you:

* **Attribute**: You must attribute any public use of the database, or works produced from the database, in the manner specified in the ODbL. For any use or redistribution of the database, or works produced from it, you must make clear to others the license of the database and keep intact any notices on the original database.
* **Share-Alike**: If you publicly use any adapted version of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL.
* **Keep open**: If you redistribute the database, or an adapted version of it, then you may use technological measures that restrict the work (such as DRM) as long as you also redistribute a version without such measures.

## Generating

Ensure you have `bash`, `curl`, `python` and `ssconvert` installed

```
# Initialize list of URLs to scrape
bash initialize.sh

# Fetch the data
bash fetch.sh

# Generate the CSVs
bash parse.sh

# Generate the aggregated CSVs
python aggregate.py
```

The fetch script sources data from DGCA (https://www.dgca.gov.in/)

## TODO

- Automatically fetch new data every month
- Parse carrier-wise domestic data tables
- Additional aggregations by city, region, carrier, date
- Visualizations of datasets

## Issues

Found an error in the data processing or have a question? Create an [issue](https://github.com/Vonter/india-aviation-traffic/issues) with the details.

## Credits

- [DGCA](https://www.dgca.gov.in/)
