import os
import time
import pandas as pd
import duckdb as db

RAW_JOINED_PATH = "data/processed/prices_with_rainfall.parquet"
DB_PATH = "data/processed/analytics.duckdb"


def build_star_schema():
    df = pd.read_parquet(RAW_JOINED_PATH)
    con = db.connect(DB_PATH)

    dim_market = df[["market"]].drop_duplicates().reset_index(drop=True)
    dim_market["market_id"] = dim_market.index
    con.execute("CREATE OR REPLACE TABLE dim_market AS SELECT * FROM dim_market")

    # TODO: build dim_commodity the same way --distinct values of the
    # "commodity" column, with a new "commodity_id" column assigned
    # from .index, written to DuckDB as a table named dim_commodity.
    dim_commodity = df[["commodity"]].drop_duplicates().reset_index(drop=True)
    dim_commodity["commodity_id"] = dim_commodity.index
    con.execute("CREATE OR REPLACE TABLE dim_commodity AS SELECT * FROM dim_commodity")

    # TODO: build the fact table. Merge `df` against BOTH dim_market and
    # dim_commodity (so every row gets a market_id AND a commodity_id),
    # then keep only these columns: id, date, market_id,
    # commodity_id, price, rainfall_mm. Write the result to DuckDB as a
    # table named fact_price_observation, using the same
    # CREATE OR REPLACE TABLE ... AS SELECT * FROM <dataframe> pattern.
    df1 = df.copy()
    df1 = df1.merge(dim_market, on="market", how="left")
    df1 = df1.merge(dim_commodity, on="commodity", how="left")
    fact_price_observation = df1[["id", "date", "market_id", "commodity_id", "price", "rainfall_mm"]]
    con.execute("CREATE OR REPLACE TABLE fact_price_observation AS SELECT * FROM fact_price_observation")

    print("\n\n=== Step 3: Star schema built ===")
    print("Fact table row count:", con.sql("SELECT COUNT(*) FROM fact_price_observation").fetchone()[0])
    con.close()

def maize_query():
    t0 = time.perf_counter()
    result = db.sql(f"""
        SELECT market, AVG(price) AS mean_price
        FROM '{RAW_JOINED_PATH}'
        WHERE commodity = 'Maize'
        GROUP BY market
        ORDER BY mean_price DESC
    """).df()
    elapsed = time.perf_counter() - t0
    print("=== Step 1: Maize query (Flat Parquet) ===")
    print(result)
    print(f"Time: {elapsed:.4f}s | File size: {os.path.getsize(RAW_JOINED_PATH)} bytes")
    return elapsed

def beans_query():
    t0 = time.perf_counter()
    result = db.sql(f"""
        SELECT market, AVG(price) AS mean_price
        FROM '{RAW_JOINED_PATH}'
        WHERE commodity = 'Beans'
        GROUP BY market
        ORDER BY mean_price DESC
    """).df()
    elapsed = time.perf_counter() - t0
    print("\n\n=== Step 2: Beans query (Flat Parquet) ===")
    print(result)
    print(f"Time: {elapsed:.4f}s | File size: {os.path.getsize(RAW_JOINED_PATH)} bytes")
    return elapsed


def run_analytical_queries():
    con = db.connect(DB_PATH)

    print("\n\n=== Step 4: Analytical queries ===")

    print("\n=== Query 1: Average price by market ===")
    print(con.sql("""
                  SELECT
                      f.market_id,
                      dm.market,
                      AVG(f.price) AS mean_price
                  FROM fact_price_observation f
                           JOIN dim_market dm ON f.market_id = dm.market_id
                  GROUP BY 
                      f.market_id,
                      dm.market
                  ORDER BY mean_price DESC
                  """).df())

    print("\n=== Query 2: Observation count by commodity ===")
    print(con.sql("""
                  SELECT 
                      f.commodity_id,
                      dc.commodity,
                      COUNT(*) AS n_observations
                  FROM fact_price_observation f
                           JOIN dim_commodity dc ON f.commodity_id = dc.commodity_id
                  GROUP BY 
                      f.commodity_id,
                      dc.commodity
                  ORDER BY n_observations DESC
                  """).df())

    # TODO:
    # add three(3) more queries of your own here,
    # each joining fact_price_observation to atleast one dimension table.
    print("\n=== Query 3: Observation count by market ===")
    print(con.sql("""
                SELECT 
                    f.market_id,
                    dm.market,
                    COUNT(*) AS n_observations
                FROM fact_price_observation f
                    JOIN dim_market dm ON f.market_id = dm.market_id
                    GROUP BY 
                        f.market_id,
                        dm.market
                    ORDER BY n_observations DESC
    """).df())

    print("\n=== Query 4: Maximum price by commodity ===")
    print(con.sql("""
                SELECT 
                    f.commodity_id, 
                    dc.commodity,
                    MAX(f.price) AS max_price
                FROM fact_price_observation f
                    JOIN dim_commodity dc ON f.commodity_id = dc.commodity_id
                    GROUP BY 
                        f.commodity_id,
                        dc.commodity
                    ORDER BY max_price DESC
    """).df())

    print("\n=== Query 5: Average rainfall by market ===")
    print(con.sql("""
             SELECT 
                 f.market_id,
                 dm.market,
                 AVG(f.rainfall_mm) AS avg_rain
             FROM fact_price_observation f
                 JOIN dim_market dm ON f.market_id = dm.market_id
                 GROUP BY
                     f.market_id,
                     dm.market
                 ORDER BY avg_rain DESC
    """).df())

    con.close()

def compare_performance():
    con = db.connect(DB_PATH)
    t0 = time.perf_counter()
    con.sql(f"""
        SELECT market, AVG(price) FROM '{RAW_JOINED_PATH}' GROUP BY market
    """).df()
    flat_time = time.perf_counter() - t0


    # TODO: time the SAME logical query -- average price per market --
    # but run it against your star schema instead: open a connection to
    # DB_PATH, join fact_price_observation to dim_market, group by
    # market, and store the elapsed time in a variable called
    # `star_time`, following the exact same timing pattern as above.
    # Close your connection when done.
    t1 = time.perf_counter()
    con.sql("""
            SELECT 
                f.market_id,
                dm.market,
                AVG(f.price) AS mean_price
            FROM fact_price_observation f
                     JOIN dim_market dm ON f.market_id = dm.market_id
            GROUP BY 
                f.market_id,
                dm.market
            ORDER BY mean_price DESC
            """).df()
    star_time = time.perf_counter() - t1



    print("\n\n=== Step 5: Performance comparison ===")
    print(f"Flat Parquet query time:  {flat_time:.4f}s")
    print(f"Star schema query time:   {star_time:.4f}s")


if __name__ == "__main__":
    maize_query()
    beans_query()
    build_star_schema()
    run_analytical_queries()
    compare_performance()
    # TODO