from common.log import Log
from common.parameters import Parameters
from renderers.renderer_factory import RendererFactory

class LogFactory:
    def create(self, params: Parameters, episode_id: int) -> Log:
        renderer_factory = RendererFactory()
        renderer = renderer_factory.create()
        return Log(renderer, params, episode_id)
