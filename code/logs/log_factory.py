from logs.log import Log
from params.parameters import Parameters
from renderers.renderer_factory import RendererFactory

class LogFactory:
    def create(self, params: Parameters) -> Log:
        renderer_factory = RendererFactory()
        renderer = renderer_factory.create()
        return Log(renderer, params)
