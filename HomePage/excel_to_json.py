import pandas as pd


csv_path = 'test_table.csv'
table_df = pd.read_csv(csv_path)
table_json = table_df.to_json('test_table.json', orient="records")
table = pd.read_json('test_table.json', orient='records')
print(table.head())