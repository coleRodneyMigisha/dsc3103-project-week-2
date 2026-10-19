What share of the rows belongs to Owino now, and why did we do this on purpose?
-
- Owino now has a size of 0.7, meaning 70% of the markets are now reading Owino, this was done on purpose to create the skewness, because skewness means a larger distribution on one side or to one entity


Which was faster, DuckDB or Spark? Roughly by how much?
-
- DuckDB was faster
- by roughly 9.5s


Nothing happened when `summary = ...` was executed. Which line actually triggered the work, and why? (Use the words *transformation* and *action*.)
-
- `summary = ...` is an initiation line, so, it doesn't execute anything
- we only see results after running `summary.explain()` and `summary.show()`
- `summary.explain()` shows how sparks plans to execute what is specified in the request, we have actions like `count` that have no physical effect on the dataframe, and transformations like `filter` and `groupBy` that completely alter the dataframe


Which of your operations caused the `Exchange` (shuffle)? Was it `filter`, `groupBy`, or `orderBy`?
-
- orderBy

Is `filter` narrow or wide? Is `groupBy` narrow or wide?
-
- `filter` is narrow
- `groupBy` is wide

Which line of the plan shows Spark only reading the columns it needs?
- 
- `Filter` and `FileScan`


After repartitioning by `market`, how uneven are the partition sizes?
-
- skewed to index 2

In a real cluster, which worker would finish last, and what does that do to total job time?
-
- I think spark would finish last because it has to first organize the data a certain way, then actually get into the desired execution


Did caching help? Would it help if only **one** action were run on `df`? Explain.
-
- Caching did not help
- Yes, because ,the way cache works, the dataframe is loaded per action, so, if it were one action, it would be loaded once and be faster


| Job | Time (s) |
|---|---|
| DuckDB, 5M rows | 0.702|
| Spark local, 5M rows | 10.234|
| Spark without cache (2 actions) | 4.851|
| Spark with cache (2 actions) | 14.646|

Recommendations
-
- **A.** A weekly report on 500,000 rows stored in one Parquet file.
  - DuckDB
- **B.** 2 TB of mobile-money transaction logs that must be processed nightly, and the job must survive machine failures.
  - Spark with cache
- **C.** A 3 GB file on a lecturer's laptop with 16 GB of RAM.
  - Spark