import pandas as pd
import re

df_initial = pd.read_json("C:/Users/lorga/Desktop/Lobby/Artikel/data raw.json", lines = True)
df_expand = pd.json_normalize(df_initial["registerEntryDetail"])
df = pd.concat([df_initial, df_expand])

# Memberships

def membership_finder(membership_list):
    if str(membership_list) == "nan":
        return "[]"
    register_list = []
    for name in membership_list:
        name = re.sub("[\(\[].*?[\)\]]", "", name)
        assorted_bits = ["(", ")", " e.V.", " e. V."]
        for assorted_bit in assorted_bits:
            name = name.replace(assorted_bit, "")
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

# Save wrangled dataset

df["name"] = df["lobbyistIdentity.name"]
df["type"] = df["activity.de"]
df["budget"] = df["financialExpensesEuro.to"]
df["memberships"] = df["membershipRegisterNumbers"]
df["zip"] = df["lobbyistIdentity.address.zipCode"]
df["registerNumber"] = df["account.registerNumber"]
df = df[["registerNumber", "name", "type", "budget", "zip", "fieldsOfInterest", "interestPercentage", "memberships"]]
df.sort_values(by = ["budget"], ascending = False, inplace = True)
df.to_csv("C:/Users/lorga/Desktop/Lobby/Artikel/data wrangled.csv", index = False)