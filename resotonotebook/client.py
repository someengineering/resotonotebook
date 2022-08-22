from abc import ABC, abstractmethod

from typing import List, Optional
from resotoclient import ResotoClient
from resotoclient.models import JsObject, JsValue
import sys


class Client(ABC):
    @abstractmethod
    async def search_list(self, search: str, section: Optional[str], graph: str) -> List[JsObject]:
        pass

    @abstractmethod
    async def search_graph(self, search: str, section: Optional[str], graph: str) -> List[JsObject]:
        pass

    @abstractmethod
    async def cli_execute(self, query: str, graph: str, section: Optional[str]) -> List[JsValue]:
        pass


class AsyncResotoClient(Client):
    def __init__(self, client: ResotoClient):
        self.client = client

    async def search_list(self, search: str, section: Optional[str], graph: str) -> List[JsObject]:
        return list(self.client.search_list(search=search, section=section, graph=graph))

    async def search_graph(self, search: str, section: Optional[str], graph: str) -> List[JsObject]:
        return list(self.client.search_graph(search=search, section=section, graph=graph))

    async def cli_execute(self, query: str, graph: str, section: Optional[str]) -> List[JsValue]:
        return list(self.client.cli_execute(command=query, graph=graph, section=section))


def get_client(url: str, psk: Optional[str]) -> Client:
    if sys.platform == "emscripten":
        # import on this level to avoid loading pyodide in the cpython context
        from resotonotebook.pyodide_client import PyodideResotoClient

        return PyodideResotoClient(url, psk)
    else:
        return AsyncResotoClient(ResotoClient(url, psk))
