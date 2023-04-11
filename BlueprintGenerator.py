'''
import unreal_engine as ue
ue.py_exec("BlueprintGenerator.py")
'''

import importlib
import json
import inspect

import LoggingUtil
importlib.reload(LoggingUtil)

import Generators.BP as BPGenerator
importlib.reload(BPGenerator)

import unreal_engine as ue
from unreal_engine.structs import EdGraphPinType

LoggingUtil.reset()

with open(r"F:\FModel\Output\Exports\Phoenix\Content\Gameplay\ToolSet\Items\Wand\BP_WandTool.json") as fp:
    nodes = json.load(fp)


def get_root_node():
    for node in nodes:
        if node.get("Type") == "BlueprintGeneratedClass":
            return node


root = get_root_node()
bp_path = root["ClassDefaultObject"]["ObjectPath"].split(".")[0]

bp = BPGenerator.BPGenerator(bp_path)

bp.clear()

bp.set_parent(ue.find_class(root["SuperStruct"]["ObjectName"]))

for node in nodes:
    if node["Type"] != "Function" or node.get("Outer") != "BP_WandTool_C" or node["Name"] in ["ExecuteUbergraph_BP_WandTool", "UserConstructionScript"]: continue
    funcFlags = BPGenerator.FunctionFlags(node["FunctionFlags"])
    if BPGenerator.FunctionFlags.FUNC_Event in funcFlags: 
        bp.add_event(node)
    else:
        bp.add_function(node)

for v in root["ChildProperties"]:
    bp.add_variable(v)


bp.compile()
LoggingUtil.reset()
bp.debug()