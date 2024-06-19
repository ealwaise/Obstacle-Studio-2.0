import pandas as pd
from src import read_write

event_data = pd.read_csv(read_write.get_path("Event Data")).set_index("ID")
event_data["Subtype"].fillna(value="Crashes SC", inplace=True)
# def change(subtype):
    # return "No crash" if subtype == "Does not crash SC" else subtype
# event_data["Subtype"] = event_data["Subtype"].apply(lambda x: change(x))

name_to_ID = {v: k for k, v in event_data["Name"].to_dict().items()}

file = open(read_write.get_path("Unit List"), 'r')
unit_list = [line.rstrip() for line in file.readlines()]
unit_list.sort()
unit_indices = {unit: i for i, unit in enumerate(unit_list)}
file.close()

file = open(read_write.get_path("Men List"), 'r')
men_list = [line.rstrip() for line in file.readlines()]
men_list.sort()
file.close()

tilesets = ["Ash",
            "Badlands",
            "Desert",
            "Ice",
            "Installation",
            "Jungle",
            "Space",
            "Twilight"]