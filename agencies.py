import pandas as pd
import json
from os import path
import re

dir = path.dirname(__file__)

df_initial = pd.read_json(path.join(dir, "data raw.json"), lines = True)
df_expand = pd.json_normalize(df_initial["registerEntryDetail"])
df_full = pd.concat([df_initial, df_expand])
df_consult = df_full.loc[df_full["activity.code"] == "ACT_CONSULTING"].reset_index().drop(columns = "index")
file_path = path.join(dir, "agencies_manual_fix.csv")
if not file_path:
    df_consult_expand = pd.json_normalize(df_consult["clientOrganizations"])
    df_consult_expand.to_csv(path.join(dir, "agencies_manual_fix.csv"), sep = ";")
else:
    df_consult_expand = pd.read_csv(file_path, sep = ";")
df = df_consult.join(df_consult_expand)

column_list = df.columns.tolist()
target_column_list = []
for column in column_list:
    if column.isdigit():
        target_column_list.append(column)
for index, row in df.iterrows():
    number = row["account.registerNumber"]
    if row["clientIdentity"] == "ORGANIZATION":
        name = str(row["lobbyistIdentity.name"])
    else:
        name = str(row["lobbyistIdentity.commonFirstName"]), str(row["lobbyistIdentity.lastName"])
        name = " ".join(name)
    print(number, name)
    for x in target_column_list:
        if row[str(x)]:
            result = str(row[str(x)])
            if result not in ["None", "nan"]:
                json_string = row[str(x)].replace("'s ", "s ").replace("O'R", "OR").replace("\'", "\"").replace("\\xa0", "")
                try:
                    tbn = json.loads(json_string)
                    df_sub = pd.json_normalize(tbn)
                    name = df_sub["name"].values
                    print(name)
                except:
                    print("Nope")
