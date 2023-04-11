import json
import LoggingUtil
import UEUtil

nodes = []
outer_name = ""

def load(path):
    global nodes, outer_name
    with open(path, "r+", encoding="utf8") as fp:
        nodes = json.load(fp)
        # Remove the _C
        outer_name = find_tree_root()["Outer"][:-2]
        

def node_has_keys(node, *keys):
    for key in keys:
        if key not in node:
            return False
    return True

def find_tree_root():
    for node in nodes:
        if node_has_keys(node, "Type", "Properties"):
            if node["Type"] == "WidgetBlueprintGeneratedClass":
                return follow_object_ref(node["Properties"]["WidgetTree"])
            

def get_by_index(index):
    return nodes[index]

def follow_object_ref(ref):
    origin, index = ref["ObjectPath"].split(".")
    origin = origin.split("/")[-1]
    if origin != outer_name and outer_name != "": 
        return None
    return get_by_index(int(index))

def get_class_for_node(node : dict):
    return UEUtil.get_class_by_path(node["Class"])



# def set_properties(obj, props, ignoreKeys = [], keyMap = {}):
#     for key in props.keys():
#         if key in ignoreKeys: continue
#         value = props[key]
#         valueTy = type(getattr(obj, keyMap.get(key, key)))
        
#         if valueTy == ue.UScriptStruct:
#             set_properties(getattr(obj, keyMap.get(key, key)), value)
#         elif valueTy == type(None) or valueTy == ue.UObject:
#             # Likely Object Ref
#             pass
#         elif type(value) == str and valueTy == int:
#             # Enum
#             pass 
#         elif valueTy in [int, float, str, bool]:
#             try:
#                 setattr(obj, keyMap.get(key, key), value)
#             except:
#                 print(key, getattr(obj, keyMap.get(key, key)), value)
#         else:
#             set_properties(getattr(obj, keyMap.get(key, key)), value, ["Hex"], {x: x.lower() for x in value.keys()})
        

def recursive_parse_node(node : dict, tree, outer, allWidgets):
    LoggingUtil.header(node["Name"])
    clz = get_class_for_node(node)

    props : dict = node.get("Properties", {})

    if clz is None:
        LoggingUtil.log(f"No Class {node['Type']}")
        LoggingUtil.undent()
        return None
    
    current_outer = tree if node["Outer"] == "WidgetTree" else outer
    widgetObj = clz(node["Name"], current_outer)

    if node["Outer"] == "WidgetTree":
        allWidgets.append(widgetObj)

    if widgetObj is None:
        LoggingUtil.undent()
        return None

    if "Slots" in props:
        newSlots = []
        for s in props["Slots"]:
            child = follow_object_ref(s)
            if child is not None: 
                newSlot = recursive_parse_node(child, tree, widgetObj, allWidgets)
                if newSlot != None: newSlots.append(newSlot)

        widgetObj.Slots = newSlots

    if "Content" in props:
        child = follow_object_ref(props["Content"])
        if child is not None:
            newWidget = recursive_parse_node(child, tree, widgetObj, allWidgets)
            if newWidget is not None: widgetObj.Content = newWidget


    # set_properties(widgetObj, props, ["Slots", "Slot", "Content", "Parent"])

    UEUtil.set_properties_by_json(widgetObj, props, ["Slots", "Slot", "Content", "Parent"])

    LoggingUtil.undent()
    return widgetObj