from typing import Dict, Optional, List
import pandas as pd
from resotoclient.models import JsObject, JsValue
import graphviz
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
from resotonotebook.client import get_client
import sys


class ResotoNotebook:
    def __init__(self, url: str, psk: Optional[str], resoto_graph: str = "resoto") -> None:
        self.client = get_client(url, psk)
        self.resoto_graph = resoto_graph

    @staticmethod
    def with_psk(psk: Optional[str]) -> "ResotoNotebook":
        return ResotoNotebook("http://localhost:8900", psk)

    async def search(self, query: str, section: Optional[str] = "reported") -> pd.DataFrame:
        iter = await self.client.search_list(search=query, section=section, graph=self.resoto_graph)

        def extract_node(node: JsObject) -> Optional[JsObject]:
            reported = node.get("reported")
            if not isinstance(reported, Dict):
                return None
            reported["account_id"] = js_find(
                node,
                ["ancestors", "account", "reported", "id"],
            )
            reported["region_id"] = js_find(
                node,
                ["ancestors", "region", "reported", "id"],
            )
            reported["cloud_id"] = js_find(
                node,
                ["ancestors", "cloud", "reported", "id"],
            )
            return reported

        nodes = [extract_node(node) for node in iter]
        return pd.DataFrame(nodes)

    async def graph(
        self,
        query: str,
        section: Optional[str] = "reported",
        engine: str = "sfdp",
        format: str = "svg",
    ) -> graphviz.Digraph:
        digraph = graphviz.Digraph(comment=query)
        digraph.format = format
        digraph.engine = engine
        digraph.graph_attr = {"rankdir": "LR", "splines": "true", "overlap": "false"}  # type: ignore
        digraph.node_attr = {  # type: ignore
            "shape": "plain",
            "colorscheme": "paired12",
        }
        cit = iter(range(0, sys.maxsize))
        colors: Dict[str, int] = defaultdict(lambda: (next(cit) % 12) + 1)

        results = await self.client.search_graph(search=query, section=section, graph=self.resoto_graph)

        for elem in results:
            if elem.get("type") == "node":
                kind = js_get(elem, ["reported", "kind"])
                color = colors[kind]
                rd = ResourceDescription(
                    id=js_get(elem, ["reported", "id"]),
                    name=js_get(elem, ["reported", "name"]),
                    uid=js_get(elem, ["id"]),
                    kind=parse_kind(kind),
                    kind_name=kind,
                )
                digraph.node(  # type: ignore
                    name=js_get(elem, ["id"]),
                    # label=rd.name,
                    label=render_resource(rd, color),
                    shape="plain",
                )
            elif elem.get("type") == "edge":
                digraph.edge(js_get(elem, ["from"]), js_get(elem, ["to"]))  # type: ignore

        return digraph

    async def cli_execute(self, query: str, section: str = "reported") -> pd.DataFrame:
        iter = await self.client.cli_execute(query, self.resoto_graph, section)

        normalize = False

        def extract_node(node: JsValue) -> Optional[JsValue]:
            if isinstance(node, dict):
                reported = node.get("reported")
                if not isinstance(reported, Dict):
                    nonlocal normalize
                    normalize = True
                    return node
                reported["account_id"] = js_find(
                    node,
                    ["ancestors", "account", "reported", "id"],
                )
                reported["region_id"] = js_find(
                    node,
                    ["ancestors", "region", "reported", "id"],
                )
                reported["cloud_id"] = js_find(
                    node,
                    ["ancestors", "cloud", "reported", "id"],
                )
                return reported
            return node

        nodes = [extract_node(node) for node in iter]
        if normalize:
            return pd.json_normalize(nodes)  # type: ignore
        else:
            return pd.DataFrame(nodes)


class ResourceKind(Enum):
    UNKNOWN = 1
    INSTANCE = 2
    VOLUME = 3
    IMAGE = 4
    FIREWALL = 5
    K8S_CLUSER = 6
    NETWORK = 7
    LOAD_BALANCER = 8
    CLOUD = 9


kind_colors = {
    ResourceKind.INSTANCE: "8",
    ResourceKind.VOLUME: "4",
    ResourceKind.IMAGE: "7",
    ResourceKind.FIREWALL: "6",
    ResourceKind.K8S_CLUSER: "5",
    ResourceKind.NETWORK: "10",
    ResourceKind.LOAD_BALANCER: "9",
    ResourceKind.CLOUD: "1",
}


@dataclass
class ResourceDescription:
    uid: str
    name: str
    id: str
    kind: ResourceKind
    kind_name: str


def render_resource(
    resource: ResourceDescription,
    color: int,
) -> str:
    return f"""\
<<TABLE STYLE="ROUNDED" COLOR="{color}" BORDER="3" CELLBORDER="1" CELLPADDING="5">
    <TR>
        <TD SIDES="B">{resource.kind_name}</TD>
    </TR>
    <TR>
        <TD SIDES="B">{resource.id}</TD>
    </TR>
    <TR>
        <TD BORDER="0">{resource.name}</TD>
    </TR>
</TABLE>>"""


do_kinds = {
    "droplet": ResourceKind.INSTANCE,
    "volume": ResourceKind.VOLUME,
    "image": ResourceKind.IMAGE,
    "firewall": ResourceKind.FIREWALL,
    "kubernetes_cluster": ResourceKind.K8S_CLUSER,
    "network": ResourceKind.NETWORK,
    "load_balancer": ResourceKind.LOAD_BALANCER,
}


def parse_kind(kind: str) -> ResourceKind:
    cloud, rest = kind.split("_")[0], "_".join(kind.split("_")[1:])
    if cloud == "digitalocean":
        return do_kinds.get(rest) or ResourceKind.UNKNOWN
    else:
        return ResourceKind.UNKNOWN


def js_find(node: JsObject, path: List[str]) -> Optional[str]:
    """
    Get a value in a nested dict.
    """
    if len(path) == 0:
        return None
    else:
        value = node.get(path[0])
        if len(path) == 1:
            return value if isinstance(value, str) else None
        if not isinstance(value, dict):
            return None
        return js_find(value, path[1:])


def js_get(node: JsObject, path: List[str]) -> str:
    result = js_find(node, path)
    if result is None:
        raise ValueError(f"Path {path} not found in {node}")
    return result
