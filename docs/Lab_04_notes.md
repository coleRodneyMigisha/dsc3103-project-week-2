**Question:** For each commodity, state the market with the highest mean price

- For maize, Bwaise had the highest mean price
- For beans, Nakasero had the highest mean price

**Question:** Write **one sentence** stating what you traded away for what you gained

- Traded having all the information in one table, gained proper and clean referencing for easy fixing of code and making of new entries


#### Notes

- Star schema separates repeated descriptive information from measurements


**Question:** State what you observe about the printed values. Is the difference small or big? Give reasons.

- The difference is small, I think this is because the star schema did not have too many more tables than the original schema of one dataset


**Question:** Write a half-page justification for whether DuckDB or plain Parquet files would be your choice going forward, and why.

- I would choose **DuckDB** for this project because the data is organized into multiple related tables using a star schema. DuckDB provides a SQL interface that makes joins, aggregations, filtering, and repeatable analytical queries convenient. It also supports a persistent database file and can query Parquet files directly when needed.

- Plain Parquet remains useful for simple, one-off analysis. It is file-based, portable, compressed, columnar, easy to share, and does not require a database server. However, as the number of related tables and analytical queries increases, managing the analysis directly from separate Parquet files becomes less convenient.

- The main reason I prefer DuckDB is therefore not only the measured speed. DuckDB provides a better structure for recurring analytical work because it supports SQL queries across the fact and dimension tables. The star schema also avoids repeatedly storing descriptive market and commodity values in every fact row. Plain Parquet would be adequate for simple one-off analysis, but DuckDB is more suitable for this project because it has multiple related tables and recurring analytical queries.
