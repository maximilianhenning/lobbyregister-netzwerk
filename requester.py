import requests

request = requests.get("https://www.lobbyregister.bundestag.de/sucheDetailJson?filter[activelobbyist][true]=true")
#request = requests.get("https://www.lobbyregister.bundestag.de/sucheDetailJson?filter[activelobbyist][true]=true&filter[fieldsofinterest][FOI_MEDIA]=true")
text = request.text

text_list = text.split("\"results\":[")

metadata = text_list[0]
metadata_list = metadata.split("}")[:-1]
metadata_new = ' '.join([x for x in metadata_list])
metadata = metadata_new + "}}}}"
with open("C:/Users/lorga/Desktop/Lobby/Artikel/metadata.json", "w", encoding="utf8") as file:
    for char in metadata:
        file.write(char)

data = text_list[1]
data = data[:-2]
with open("C:/Users/lorga/Desktop/Lobby/Artikel/data raw.json", "w", encoding="utf8") as file:
    for char in data:
        file.write(char)