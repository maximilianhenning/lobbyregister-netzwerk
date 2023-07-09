import pandas as pd
import re
from os import path

dir = path.dirname(__file__)
df_initial = pd.read_json(path.join(dir, "data raw.json"), lines = True)
df_expand = pd.json_normalize(df_initial["registerEntryDetail"])
df = pd.concat([df_initial, df_expand])
df_contracting_expand = pd.json_normalize(df_expand["clientOrganizations"])
df = df.join(df_contracting_expand)

# Memberships

global progress_counter
progress_counter = 0
completion_count = len(df["lobbyistIdentity.membershipEntries"].tolist())
def membership_finder(membership_list):
    global progress_counter 
    progress_counter += 1
    print(str((progress_counter / completion_count)*100)[:5], "%")
    if str(membership_list) == "nan":
        return "[]"
    register_list = []
    for name in membership_list:
        # Remove content in normal and square brackets
        name = re.sub("[\(\[].*?[\)\]]", "", name)
        # Remove extra brackets as well as e.V. and e. V.
        name = re.sub("\(|\)|e\.V\.|e\. V\.", "", name)
        retrieved_index = df.loc[df["lobbyistIdentity.name"].str.contains(name, na = False) == True].index.values.astype(int)
        if retrieved_index.any():
            retrieved_index = retrieved_index[0]
        if retrieved_index.any():
            retrieved_register = df.loc[retrieved_index]["registerNumber"].values.astype(str)[0]
            register_list.append(retrieved_register)
    return register_list
df["membershipRegisterNumbers"] = df["lobbyistIdentity.membershipEntries"].apply(membership_finder)

# Interests

def interest_reader(foi_old):
    if str(foi_old) == "nan":
        return "nan"
    foi_normalized = pd.json_normalize(foi_old)
    foi_codes = foi_normalized["code"]
    foi_list = foi_codes.tolist()
    return foi_list
df["fieldsOfInterest"] = df["fieldsOfInterest"].apply(interest_reader)

# Interest percentage

def interest_calc(interest_list_input):
    actual_interests = ["FOI_ECONOMY_ECOMMERCE", 
                        "FOI_IS_CYBER", 
                        "FOI_MEDIA_COMMUNICATION", 
                        "FOI_MEDIA_COPYRIGHT", 
                        "FOI_MEDIA_DIGITALIZATION", 
                        "FOI_MEDIA_INTERNET_POLICY", 
                        "FOI_MEDIA_PRIVACY", 
                        "FOI_SA_PUBLIC_ADMINISTRATION"]
    interest_list = []
    for interest in interest_list_input:
        if "|" in interest:
            interest = interest.split("|")[1]
        interest_list.append(interest)
    list_length = len(interest_list)
    counter = 0
    for interest in interest_list:
        if interest in actual_interests:
            counter += 1
    interest_percentage = counter / list_length
    return interest_percentage
df["interestPercentage"] = df["fieldsOfInterest"].apply(interest_calc)

# Simplify type

def type_simplifier(activity_code):
    if activity_code == "ACT_ORGANIZATION":
        return "Unternehmen"
    elif activity_code in ["ACT_TRADE_ASSOC", "ACT_PROFESSION_ASSOC", "ACT_PRIVATE_ORGA", "ACT_NONPROFIT_ORGA"]:
        return "Verein/Verband"
    elif activity_code == "ACT_CONSULTING":
        return "Consulting"
    else:
        return "nan"
df["type"] = df["activity.code"].apply(type_simplifier)

# Save wrangled overall dataset

df["name"] = df["lobbyistIdentity.name"]
df["budget"] = df["financialExpensesEuro.to"]
df["memberships"] = df["membershipRegisterNumbers"]
df["zip"] = df["lobbyistIdentity.address.zipCode"]
df["registerNumber"] = df["account.registerNumber"]
target_column_list = ["name", "type", "budget", "memberships", "zip", "registerNumber", "interestPercentage"]
for column in df.columns:
    if type(column) == int:
        target_column_list.append(column)
df = df[target_column_list]
df.sort_values(by = ["budget"], ascending = False, inplace = True)
df.to_csv(path.join(dir, "data wrangled.csv"), index = False)