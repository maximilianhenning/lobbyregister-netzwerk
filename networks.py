import pandas as pd
from collections import Counter
from os import path

dir = path.dirname(__file__)
df = pd.read_csv(path.join(dir, "data wrangled.csv"))

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

# Contractors

# XXXX

# Create final dataset with only organisations with above 0.15 interest percentage,
# or with more than four such organisations as members,
# or that has contracted or been contracted by such an organisation

percentage_df = df[df["interestPercentage"] > 0.15]
def member_counter(dict):
    memberships_with_interest_list = []
    for org in memberships_dict:
        counter = 0
        for member in memberships_dict[org]:
            if member in percentage_df["registerNumber"].values:
                counter += 1
        if counter > 4:
            memberships_with_interest_list.append(org)
    return memberships_with_interest_list
memberships_with_interest_list = member_counter(memberships_dict)
membership_df = df[df["registerNumber"].isin(memberships_with_interest_list)]
# XXXX Add contractors

# Save final overall dataset

final_df = pd.concat([percentage_df, membership_df]).drop_duplicates().reset_index(drop=True)
final_df.sort_values(by = ["budget"], ascending = False, inplace = True)
final_df.to_csv(path.join(dir, "data.csv"), index = False)

# Save overall edges

membership_edges_list = [edge for edge in membership_edges_list if edge[0] in final_df["registerNumber"].values and edge[1] in final_df["registerNumber"].values ]
edges_df = pd.DataFrame(membership_edges_list, columns = ["Source", "Target"])
edges_df["Type"] = "Directed"
edges_df.to_csv(path.join(dir, "edges.csv"), index = False)

# Save overall nodes

nodes_df = final_df[["registerNumber", "name", "activity_code", "activity", "budget", "zip", "interestPercentage"]]
nodes_df.rename(columns = {"registerNumber": "Id", "name": "Label"}, inplace = True)
nodes_df.to_csv(path.join(dir, "nodes.csv"), index = False)
