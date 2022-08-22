# type: ignore
import pyodide
import js
from typing import Optional, List, Dict
from resotoclient import rnd_str
from resotoclient.jwt_utils import encode_jwt_to_headers
from resotonotebook.client import Client
from resotoclient.models import JsObject, JsValue


class PyodideResotoClient(Client):
    def __init__(self, url: str, psk: Optional[str]):
        self.url = url
        self.psk = psk
        self.session_id = rnd_str()

    def headers(self) -> Dict[str, str]:

        headers = {"Content-type": "application/json", "Accept": "application/json"}

        if self.psk:
            encode_jwt_to_headers(headers, {}, self.psk)

        return headers

    async def search_list(self, search: str, section: Optional[str], graph: str) -> List[JsObject]:
        path = f"/graph/{graph}/search/list"

        url = js.URL.new(path, js.location.origin)
        if section:
            url.searchParams.append("section", section)
        url.searchParams.append("session_id", self.session_id)

        headers = self.headers()

        options = {"method": "POST", "body": search, "headers": headers}

        async def call(url, options):
            response = await js.fetch(url, options)

            if response.status == 200:
                json = await response.json()
                return json.to_py()
            else:
                text = await response.text()
                raise AttributeError(text)

        options = pyodide.ffi.to_js(options, dict_converter=js.Object.fromEntries)

        return await call(url, options)

    async def search_graph(self, search: str, section: Optional[str], graph: str) -> List[JsObject]:
        path = f"/graph/{graph}/search/graph"

        url = js.URL.new(path, js.location.origin)
        if section:
            url.searchParams.append("section", section)
        url.searchParams.append("session_id", self.session_id)

        headers = self.headers()

        options = {"method": "POST", "body": search, "headers": headers}

        async def call(url, options):
            response = await js.fetch(url, options)

            if response.status == 200:
                json = await response.json()
                return json.to_py()
            else:
                text = await response.text()
                raise AttributeError(text)

        options = pyodide.ffi.to_js(options, dict_converter=js.Object.fromEntries)

        return await call(url, options)

    async def cli_execute(self, query: str, graph: str, section: Optional[str]) -> List[JsValue]:
        path = "/cli/execute"

        url = js.URL.new(path, js.location.origin)
        if section:
            url.searchParams.append("section", section)
        url.searchParams.append("graph", graph)
        url.searchParams.append("session_id", self.session_id)

        headers = self.headers()
        headers["Content-type"] = "text/plain"

        options = {"method": "POST", "body": query, "headers": headers}

        async def call(url, options):
            response = await js.fetch(url, options)

            if response.status == 200:
                content_type = response.headers.get("Content-Type")
                if content_type == "text/plain":
                    text = await response.text()
                    return [text.to_py()]
                elif content_type == "application/json":
                    json = (await response.json()).to_py()
                    if isinstance(json, list):
                        return json
                    return [json]
                else:
                    msg = f"Content type {content_type} is not supported in "
                    +"jupyterlite version of resotonotebook. Use a jupyter notebook instead"
                    raise NotImplementedError(msg)
            else:
                raise AttributeError(response.text)

        options = pyodide.ffi.to_js(options, dict_converter=js.Object.fromEntries)

        return await call(url, options)
