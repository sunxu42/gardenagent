import os
from typing import Any, NotRequired, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langgraph.prebuilt import ToolRuntime
from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, AgentState
from deepagents.backends.protocol import BACKEND_TYPES, BackendProtocol
from deepagents.middleware._utils import append_to_system_message

AGENTS_MD = "./AGENTS.md"
USER_MD = "./USER.md"
SOUL_MD = "./SOUL.md"
IDENTITY_MD = "./IDENTITY.md"
BOOTSTRAP_MD = "./BOOTSTRAP.md"
HEARTBEAT_MD = "./HEARTBEAT.md"
PROJECT_CONTEXT = """
# Project Context
The following project context files have been loaded:
If SOUL.md is present, embody its persona and tone. Avoid stiff, generic replies; follow its guidance unless higher-priority instructions override it.
"""
CONTEXT_FILES = [AGENTS_MD, SOUL_MD, USER_MD, IDENTITY_MD, HEARTBEAT_MD, BOOTSTRAP_MD]
class ContextState(AgentState):
    project_context: str

class ProjectContextUpdate(TypedDict):
    project_context: str


def _load_context(backend: BackendProtocol, source_path: str):
    cxt = PROJECT_CONTEXT
    results = backend.download_files(CONTEXT_FILES)
    for result in results:
        if result.content is None:
            continue
        try:
            content = result.content.decode("utf-8")
            cxt += f"\n##{result.path}\n{content}"
        except UnicodeDecodeError as e:
            continue
        

    return cxt



async def _aload_context(backend: BackendProtocol, source_path: str):
    cxt = PROJECT_CONTEXT
    results = await backend.adownload_files(CONTEXT_FILES)
    for result in results:
        if result.content is None:
            continue
        try:
            content = result.content.decode("utf-8")
            cxt += f"\n##{result.path}\n{content}"
        except UnicodeDecodeError as e:
            continue
    return cxt



class ContextMiddleware(AgentMiddleware[ContextState, Any]):
    state_schema = ContextState

    def __init__(self, *, backend: BACKEND_TYPES, source_path: str) -> None:
        self._backend = backend
        self.source_path = source_path
    
    def _get_backend(self, state: ContextState, runtime: Runtime, config: RunnableConfig) -> BackendProtocol:
        if callable(self._backend):
            # Construct an artificial tool runtime to resolve backend factory
            tool_runtime = ToolRuntime(
                state=state,
                context=runtime.context,
                stream_writer=runtime.stream_writer,
                store=runtime.store,
                config=config,
                tool_call_id=None,
            )
            backend = self._backend(tool_runtime)  # ty: ignore[call-top-callable, invalid-argument-type]
            if backend is None:
                msg = "ContextMiddleware requires a valid backend instance"
                raise AssertionError(msg)
            return backend

        return self._backend


    def before_agent(self, state: ContextState, runtime, config: RunnableConfig):
        backend = self._get_backend(state, runtime, config)
        cxt = _load_context(backend, self.source_path)
        return ProjectContextUpdate(project_context=cxt)

    async def abefore_agent(self, state: ContextState, runtime, config: RunnableConfig):
        backend = self._get_backend(state, runtime, config)
        cxt = await _aload_context(backend, self.source_path)
        return ProjectContextUpdate(project_context=cxt)
                   
    def modify_request(self, request: ModelRequest) -> ModelRequest:

        new_system_message = append_to_system_message(request.system_message, request.state.get("project_context"))
    
        return request.override(system_message=new_system_message)

        
    def wrap_model_call(self, request: ModelRequest, handler):
        modified = self.modify_request(request)
        return handler(modified)

    async def awrap_model_call(self, request: ModelRequest, handler):
        modified = self.modify_request(request)
        return await handler(modified)