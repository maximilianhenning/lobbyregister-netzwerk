import pandas as pd
from collections import Counter
from os import path
import json
import re

dir = path.dirname(__file__)
df = pd.read_csv(path.join(dir, "data wrangled.csv"))

# Contractors

target_column_list = []
for column in df.columns.tolist():
    if column.isdigit():
        target_column_list.append(str(column))
contract_dict = {}

for index, row in df.iterrows():
    register_number = row["registerNumber"]
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
                        retrieved_index_array = df.index[df["name"].str.contains(contractor_name, na = False) == True]
                        if retrieved_index_array.size > 0:
                            retrieved_index = retrieved_index_array[0]
                        if "retrieved_index" in locals():
                            contractor_register_number = df.loc[retrieved_index]["registerNumber"].values.astype(str)[0]
                            del retrieved_index
                            contractor_list.append(contractor_register_number)
                except Exception as e:
                    pass
                    #print(e)
    contract_dict[register_number] = contractor_list

# Memberships

membership_edges_table = []
membership_edges_list = []
memberships_dict = {}

def membership_edge_creator(registerNumber, memberships):
    membership_edges_list = []
    if memberships == "nan":
        return membership_edges_list
    memberships = memberships.strip("][").split(", ")
    for membership in memberships:
        if membership:
            membership = membership.replace("'", "")
            membership_edges_list.append([registerNumber, membership])
    return membership_edges_list
membership_edges_table = df.apply(lambda x: membership_edge_creator(x.registerNumber, x.memberships), axis = 1)

for line in membership_edges_table:
    for list in line:
        membership_edges_list.append(list)
        if not list[1] in memberships_dict:
            memberships_dict[list[1]] = [list[0]]
        else:
            memberships_dict[list[1]].append(list[0])

# Create final dataset with only organisations with above 0.15 interest percentage...

percentage_df = df.loc[df["interestPercentage"] > 0.15]
organisations_with_percentage = percentage_df["registerNumber"].tolist()

# ...or that has contracted or been contracted by such an organisation...

contractor_edges_list = []
for key in contract_dict.keys():
    if key in organisations_with_percentage:
        for org in contract_dict[key]:
            contractor_edges_list.append([key, org])
    else:
        if contract_dict[key]:
            for org in contract_dict[key]:
                if org in organisations_with_percentage:
                    contractor_edges_list.append([key, org])
contractors_list = []
for edge in contractor_edges_list:
    contractors_list.append(contractor_edges_list[0])
    contractors_list.append(contractor_edges_list[1])
contractor_df = df.loc[df["registerNumber"].isin(contractors_list)]

# ...or with more than four such organisations as members

def member_counter(dict):
    memberships_with_interest_list = []
    for org in memberships_dict:
        counter = 0
        for member in memberships_dict[org]:
            if member in organisations_with_percentage:
                counter += 1
        if counter > 4:
            memberships_with_interest_list.append(org)
    return memberships_with_interest_list
memberships_with_interest_list = member_counter(memberships_dict)
membership_df = df.loc[df["registerNumber"].isin(memberships_with_interest_list)]

# Assemble final dataset

final_df = pd.concat([percentage_df, contractor_df, membership_df], ignore_index = True).drop_duplicates().reset_index(drop=True)
final_df.sort_values(by = ["budget"], ascending = False, inplace = True)

# Save edges

membership_edges_list = [edge for edge in membership_edges_list if edge[0] in final_df["registerNumber"].values and edge[1] in final_df["registerNumber"].values ]
membership_edges_df = pd.DataFrame(membership_edges_list, columns = ["Source", "Target"])
membership_edges_df["Class"] = "membership"
contractor_edges_df = pd.DataFrame(contractor_edges_list, columns = ["Source", "Target"])
contractor_edges_df["Class"] = "contractor"
edges_df = pd.concat([membership_edges_df, contractor_edges_df])
edges_df["Type"] = "Directed"
edges_df.to_csv(path.join(dir, "edges.csv"), index = False)

# Save nodes

nodes_df = final_df[["registerNumber", "name", "type", "budget", "zip", "interestPercentage"]]
nodes_df.rename(columns = {"registerNumber": "Id", "name": "Label"}, inplace = True)
nodes_df.to_csv(path.join(dir, "nodes.csv"), index = False)