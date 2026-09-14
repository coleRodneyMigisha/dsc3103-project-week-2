def merge_data(clean_df, rain_df):
    merged = clean_df.merge(rain_df, how='left', on=['date', 'market'])

    return merged