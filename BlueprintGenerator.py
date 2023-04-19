'''
import unreal_engine as ue
ue.py_exec("BlueprintGenerator.py")
'''

import importlib

import LoggingUtil
importlib.reload(LoggingUtil)

import Tools.Blueprint as BPGenerator
importlib.reload(BPGenerator)

import Tools.FModel
importlib.reload(Tools.FModel)

import Tools.UE as UETools
importlib.reload(UETools)

import unreal_engine as ue
LoggingUtil.reset()

# JSON_PATH = r"F:\FModel\Output\Exports\Phoenix\Content\Gameplay\ToolSet\Items\Wand\BP_WandTool.json"
JSON_PATH = r"F:\FModel\Output\Exports\Phoenix\Content\CustomContent\TestActor.json"

fmodel = Tools.FModel.FModelJson(JSON_PATH)


root = fmodel.get_first_of_key("Type", "BlueprintGeneratedClass")
bp_path = root["ClassDefaultObject"]["ObjectPath"].split(".")[0]

bp = BPGenerator.BPGenerator(bp_path)

bp.clear()

bp.set_parent(ue.find_class(root["SuperStruct"]["ObjectName"]))

bp.add_vars(root["ChildProperties"])

def is_function(node):
    return not (node["Type"] != "Function" or node.get("Outer") != root.get("Name") or node.get("Name") in ["ExecuteUbergraph_BP_WandTool", "UserConstructionScript"])

for node in fmodel[is_function]:
    funcFlags = BPGenerator.FunctionFlags(node["FunctionFlags"])
    if node.get("Name").endswith("__DelegateSignature"):
        bp.add_event_delegate(node)
    elif BPGenerator.FunctionFlags.FUNC_Event in funcFlags: 
        bp.add_event(node)
    else:
        bp.add_function(node)


# graph = ue.blueprint_add_event_dispatcher(bp.bp, "NewEventDispatcher")
# print(graph)

bp.compile()
LoggingUtil.reset()
# bp.debug()

bp.load_defaults()
defaults = fmodel.get_first_of_key("Type", root["Name"])["Properties"]
# bp.default_object.get_property("ComboSplitData").SplitFrame = 2
# fprop = bp.default_object.get_fproperty("ComboAnimationTags")
# print(fprop.get_inner().convert())
# print(fprop.get_type_str())
bp.save_defaults()

# <unreal_engine.UObject 'TestEventDispatcher' (0x000001F788927340) UClass 'EdGraph' (refcnt: 2)>
# K2Node_FunctionEntry

# LoggingUtil.debug_object_properties(bp.bp)
# dg = bp.bp.DelegateSignatureGraphs[0]
# for pin in dg.Nodes[0].node_pins():
#     print(pin)