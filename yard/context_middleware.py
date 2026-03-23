from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, AgentState


class ContextMiddleware(AgentMiddleware):

    def __init__(self):
        pass

    def before_agent(self, state: AgentState, runtime):
        return state

    async def abefore_agent(self, state: AgentState, runtime):
        return state                 


    # def modify_request(self, request: ModelRequest) -> ModelRequest:
    #     print(request)
    #     return request

        
    # def wrap_model_call(self, request: ModelRequest, handler):
    #     modified = self.modify_request(request)
    #     return handler(modified)

    # async def awrap_model_call(self, request: ModelRequest, handler):
    #     modified = self.modify_request(request)
    #     return await handler(modified)