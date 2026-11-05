What share of the rows belongs to Owino now, and why did we do this on purpose?
-
- Owino now has a size of 0.7, meaning 70% of the markets are now reading Owino (`3,500,259` out of `5,000,000` rows). This was done on purpose to create data skewness, because skewness means a larger distribution on one side or to one entity, allowing us to observe uneven partition sizes during a shuffle.


Which was faster, DuckDB or Spark? Roughly by how much?
-
- DuckDB was faster (`1.389s` vs `11.205s`, or `0.702s` vs `10.234s` on earlier run)
- by roughly `9.5s` to `9.8s` (about 8x–14x faster on a single laptop).


Nothing happened when `summary = ...` was executed. Which line actually triggered the work, and why? (Use the words *transformation* and *action*.)
-
- `summary = ...` only builds a logical plan of lazy *transformations* (`filter`, `groupBy`, `agg`, `orderBy`), so it doesn't execute anything immediately.
- We only see physical execution triggered when `summary.show()` is called, because `show()` is an *action* that forces Spark to compile and execute the DAG across partitions (`summary.explain()` only prints the execution plan without scanning the rows).


Which of your operations caused the `Exchange` (shuffle)? Was it `filter`, `groupBy`, or `orderBy`?
-
- Both `groupBy` (`Exchange hashpartitioning(market, 200)`) and `orderBy` (`Exchange rangepartitioning(mean_price DESC, 200)`) caused an `Exchange` (shuffle).

Is `filter` narrow or wide? Is `groupBy` narrow or wide?
-
- `filter` is narrow (each partition can filter its own rows independently without moving data across partitions).
- `groupBy` is wide (all rows with the same `market` key must be shuffled to the same partition to compute the final aggregate).

Which line of the plan shows Spark only reading the columns it needs?
-
- `FileScan parquet [market#2,price#4L] ... ReadSchema: struct<market:string,price:bigint>` (column pruning) and `PushedFilters: [IsNotNull(price)]` (predicate pushdown).


After repartitioning by `market`, how uneven are the partition sizes?
-
- Highly uneven and skewed to partition index `2` (`pid=2` holds `4,088,959` rows because `Owino` plus hash-colliding markets land there, while partitions `0`, `1`, and `5` hold ~`300,000` rows each, and partitions `3` and `4` hold `0` rows).

In a real cluster, which worker would finish last, and what does that do to total job time?
-
- The worker assigned to partition `2` (holding `Owino`'s 4.08M rows) would finish last (a straggler task). Because a stage is only complete when its slowest task finishes, all other workers sit idle waiting for that one overloaded worker, inflating total job time.


Did caching help? Would it help if only **one** action were run on `df`? Explain.
-
- Caching did not help here (`use_cache=False: 3.041s` vs `use_cache=True: 8.845s`) because reading from local Parquet with column pruning is already very fast, while `.cache()` materialises the entire filtered DataFrame (all columns) in memory first, which costs more overhead than re-reading the needed column from Parquet.
- If only **one** action were run on `df`, caching would never help and would only hurt performance, because you pay the extra memory materialisation cost during that single action without ever reusing the cached partitions a second time.


| Job | Time (s) |
|---|---|
| DuckDB, 5M rows | 0.702 (1.389) |
| Spark local, 5M rows | 10.234 (11.205) |
| Spark without cache (2 actions) | 3.041 (4.851) |
| Spark with cache (2 actions) | 8.845 (14.646) |

Recommendations (Decision Memo)
-
- **A. A weekly report on 500,000 rows stored in one Parquet file:**
  - **Recommendation: DuckDB.** In our benchmark on 5 million rows (10x larger than 500,000 rows), DuckDB finished in ~0.7–1.4 seconds compared to Spark's ~10–11 seconds. Starting a Spark session, building a distributed plan, and shuffling across partitions introduces fixed JVM and scheduling overhead that a 500k-row file never recovers. DuckDB runs in-process with vectorised columnar execution and zero cluster setup.
- **B. 2 TB of mobile-money transaction logs that must be processed nightly, and the job must survive machine failures:**
  - **Recommendation: Spark (on a multi-node cluster).** A 2 TB dataset exceeds a single machine's memory and I/O bandwidth ceiling, requiring horizontal scaling across multiple worker nodes. Furthermore, nightly production jobs on 2 TB require fault tolerance: if a worker node fails mid-run, Spark uses lineage to recompute only the lost partitions on another worker rather than restarting the entire 2 TB job from scratch.
- **C. A 3 GB file on a lecturer's laptop with 16 GB of RAM:**
  - **Recommendation: DuckDB.** A 3 GB file fits comfortably within a 16 GB RAM laptop (and DuckDB can also spill out-of-core if needed). Running Spark in `local[*]` mode on a single laptop still pays serialization, shuffle, and JVM overhead without adding extra machines, whereas DuckDB will query the 3 GB Parquet/CSV directly across all local CPU cores in seconds.
