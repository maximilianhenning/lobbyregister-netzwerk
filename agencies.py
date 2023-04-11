import pandas as pd
import json
from os import path
import re

dir = path.dirname(__file__)

df_initial = pd.read_json(path.join(dir, "data raw.json"), lines = True)
df_expand = pd.json_normalize(df_initial["registerEntryDetail"])
df_full = pd.concat([df_initial, df_expand])
df_consult = df_full.loc[df_full["activity.code"] == "ACT_CONSULTING"].reset_index().drop(columns = "index")
file_path = path.join(dir, "agencies_manual_fix2.csv")
df_consult_expand = pd.json_normalize(df_consult["clientOrganizations"])
df = df_consult.join(df_consult_expand)

column_list = df.columns.tolist()
target_column_list = []
for column in column_list:
    if type(column) == int:
        target_column_list.append(column)
contract_dict = {}
for index, row in df.iterrows():
    register_number = row["account.registerNumber"]
    if row["clientIdentity"] == "ORGANIZATION":
        name = str(row["lobbyistIdentity.name"])
    else:
       name = str(row["lobbyistIdentity.commonFirstName"]), str(row["lobbyistIdentity.lastName"])
       name = " ".join(name)
    contractor_list = []
    for x in target_column_list:
        if row[x]:
            result = str(row[x])
            if result not in ["None", "nan"]:
                json_string = result.replace("'s ", "s ").replace("O'R", "OR").replace("\'", "\"").replace("\\xa0", "")
                try:
                    tbn = json.loads(json_string)
                    df_sub = pd.json_normalize(tbn)
                    # If it has a working reference, get that
                    if "clientReferenceUrl" in df_sub.columns.tolist():
                        contractor_register_number = str(df_sub["clientReferenceUrl"].values).split("suche/")[1].strip("']")
                        contractor_list.append(contractor_register_number)
                    # Otherwise, try to find the name
                    else:
                        contractor_name = re.sub(r"['\[\]]", "", str(df_sub["name"].values))
                        # df names will need to be changed when incorporated into wrangling
                        retrieved_index_array = df_full.index[df_full["lobbyistIdentity.name"].str.contains(contractor_name, na = False) == True]
                        if retrieved_index_array.size > 0:
                            retrieved_index = retrieved_index_array[0]
                        if "retrieved_index" in locals():
                            contractor_register_number = df_full.loc[retrieved_index]["registerNumber"].values.astype(str)[0]
                            del retrieved_index
                            contractor_list.append(contractor_register_number)
                except Exception as e:
                    print(e)
    for contractor in contractor_list:
        if contractor in contract_dict.keys():
            contract_dict[contractor].append(register_number)
        else:
            contract_dict[contractor] = [register_number]
print(contract_dict)
print(len(contract_dict.keys()))