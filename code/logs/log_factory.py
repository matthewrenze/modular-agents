from artifacts.artifacts import Artifacts
from logs.log import Log
from params.parameters import Parameters
from renderers.render import Renderer

class LogFactory:
    def create(self, renderer: Renderer, artifacts: Artifacts, params: Parameters) -> Log:
        folder_path = artifacts.create_episode(params)
        file_name = artifacts.get_file_name(params, "log.txt")
        file_path = f"{folder_path}/{file_name}"
        file = open(file_path, "w", encoding="utf-8", newline="\n")
        return Log(file, renderer)
