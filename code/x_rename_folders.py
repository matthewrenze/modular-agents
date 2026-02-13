import os

# Rename all folders (not files) in data/details:
# from "[agent_name] - [model_name] - [eval_name]"
# to "[model_name] - [agent_name] - [eval_name]"

def rename_folders(folder_path):
    for folder_name in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, folder_name)):
            parts = folder_name.split(" - ")
            if not len(parts) == 3:
                continue

            agent_name, model_name, eval_name = parts
            new_folder_name = f"{model_name} - {agent_name} - {eval_name}"
            os.rename(os.path.join(folder_path, folder_name), os.path.join(folder_path, new_folder_name))
            print(f"Renamed '{folder_name}' to '{new_folder_name}'")


def rename_files(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if not file_name.endswith(".csv"):
            continue

        parts = file_name.split(" - ")
        if not len(parts) == 3:
            continue

        agent_name, model_name, eval_name = parts
        new_file_name = f"{model_name} - {agent_name} - {eval_name}"
        os.rename(file_path, f"{folder_path}/{new_file_name}")
        print(f"Renamed '{file_name}' to '{new_file_name}'")

# rename_folders("../data/details")
# rename_folders("../data/logs")
# rename_folders("../data/messages")
# rename_folders("../data/reviews")
# rename_folders("../data/states")
# rename_files("../data/results")






