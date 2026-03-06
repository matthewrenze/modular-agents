from states.reader.state_reader import StateReader

file_path = "states/test_file.yaml"
reader = StateReader()
state = reader.read(file_path)

print(state)