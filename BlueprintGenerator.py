'''
import unreal_engine as ue
ue.py_exec("BlueprintGenerator.py")
'''

import importlib

import LoggingUtil
importlib.reload(LoggingUtil)

import Tools.Blueprint as BPGenerator
importlib.reload(BPGenerator)

import Tools.FModel as FTools
importlib.reload(FTools) 

import Tools.UE as UETools
importlib.reload(UETools)

import unreal_engine as ue
LoggingUtil.reset()

# JSON_PATH = r"F:\FModel\Output\Exports\Phoenix\Content\Gameplay\ToolSet\Items\Wand\BP_WandTool.json"
JSON_PATH = r"F:\FModel\Output\Exports\Phoenix\Content\CustomContent\TestActor.json"

fmodel = FTools.FModelJson(JSON_PATH)


root = fmodel.get_first_of_key("Type", "BlueprintGeneratedClass")
bp_path = root["ClassDefaultObject"]["ObjectPath"].split(".")[0]


bp = BPGenerator.BPGenerator(bp_path, fmodel)

bp.clear()

bp.set_parent(UETools.find_object(root["SuperStruct"]))

bp.add_vars(root["ChildProperties"])

def is_function(node):
    return not (
        node.get("Type") != "Function" or
        node.get("Outer") != root.get("Name") or
        node.get("Name").startswith("ExecuteUbergraph") or 
        node.get("Name") in tuple("UserConstructionScript")
    )

for node in fmodel[is_function]:
    funcFlags = UETools.FunctionFlags(node["FunctionFlags"])

    # Event binding to a delegate
    if node.get("Name").startswith("BndEvt__"):
        pass
    elif node.get("Name").endswith("__DelegateSignature"):
        bp.add_event_delegate(node)
    elif UETools.FunctionFlags.FUNC_Event in funcFlags: 
        bp.add_event(node)
    else:
        bp.add_function(node)

bp.add_components()

bp.compile()
LoggingUtil.reset()
# bp.debug()

bp.load_defaults()
defaults = fmodel.get_first_of_key("Type", root["Name"])["Properties"]

allNotSet = []

LoggingUtil.header("Setting Defaults")
for key in defaults:
    didSet = bp.set_default_value(key, defaults[key])
    if not didSet: allNotSet.append(key)
LoggingUtil.undent()

print(allNotSet)

# TODO Set properties in components


bp.save_defaults()