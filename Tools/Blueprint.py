import unreal_engine as ue
from unreal_engine.classes import BlueprintFactory, Blueprint, K2Node_FunctionResult, K2Node_Event, K2Node_CustomEvent
from unreal_engine.structs import EdGraphPinType, BPVariableDescription, EdGraphTerminalType
from unreal_engine.enums import EEdGraphPinDirection, EPinContainerType

import Tools.UE as UETools
import Tools.FModel

import LoggingUtil

def get_generated_components(fmodel : Tools.FModel.FModelJson):
    cmps = []
    for scs_node in fmodel.get_all_of_key("Type", "SCS_Node"):
        props = scs_node["Properties"]
        if props["ComponentClass"]["ObjectName"] == "Class'SceneComponent'": continue
        cmp_type = props["ComponentClass"]["ObjectName"][:-1].split("'")[-1]
        var_name = props["InternalVariableName"]
        prop_name = props["ComponentTemplate"]["ObjectName"].split(":")[-1][:-1]
        cmps.append({
            "Type": cmp_type,
            "VarName": var_name,
            "RealName": prop_name,
            "Class": UETools.find_object(props["ComponentClass"])
        })

    return cmps


def get_parent_components(fmodel : Tools.FModel.FModelJson):
    cmps = []
    root = fmodel.get_first_of_key("Type", "BlueprintGeneratedClass")
    default_node = fmodel.get_first_of_key("Type", root["Name"])
    default_name = default_node["Name"]
    defaults = default_node["Properties"]

    def is_json_component(json_value):
        if not isinstance(json_value, dict): return False
        if ("ObjectName" not in json_value) or ("ObjectPath" not in json_value): return False
        return f"'{default_name}:" in json_value["ObjectName"]

    for key in [k for k in defaults if is_json_component(defaults[k])]:
        v = defaults[key]

        cmps.append({
            "VarName": v["ObjectName"].split(":")[-1][:-1],
            "RealName": key,
        })

    return cmps

class BPGenerator():
    path = ""
    bp : Blueprint = None
    default_object = None
    bp_vars = []
    generated_components = []
    parent_components = []

    fmodel : Tools.FModel.FModelJson

    def __init__(self, path : str, fmodel : Tools.FModel.FModelJson):
        self.fmodel = fmodel
        self.path = path
        try:
            self.bp = ue.load_object(Blueprint, path)
        except:
            self.bp = BlueprintFactory().factory_create_new(path)

        self.generated_components = get_generated_components(self.fmodel)
        self.parent_components = get_parent_components(self.fmodel)
        self.modify()

    def is_var_component(self, var_name : str):
        for cmp in self.generated_components:
            if cmp["VarName"] == var_name: return True
        return False

    def is_real_var_parent_component(self, real_var_name : str):
        for cmp in self.parent_components:
            if cmp["RealName"] == real_var_name: return True
        return False

    def modify(self):
        self.bp.modify()

    def compile(self):
        ue.blueprint_mark_as_structurally_modified(self.bp)
        self.bp.post_edit_change()
        ue.compile_blueprint(self.bp)

    def recompile(self):
        self.compile()
        self.modify()

    def clear(self):
        # Clear all functions
        self.bp.FunctionGraphs = [
            func for func in self.bp.FunctionGraphs if func.get_name() == "UserConstructionScript"
        ]

        self.bp.DelegateSignatureGraphs = []

        # Clear EventGraph
        self.bp.UbergraphPages = [
            page for page in self.bp.UbergraphPages if page.get_name() == "EventGraph"
        ]

        for node in self.bp.UberGraphPages[0].Nodes:
            self.bp.UberGraphPages[0].graph_remove_node(node)

        # Clear existing variables
        self.bp.NewVariables = []

        for cmp in ue.get_blueprint_components(self.bp):
            ue.remove_component_from_blueprint(self.bp, cmp.get_name())

        self.recompile()

    def apply_variables(self):
        self.bp.NewVariables = self.bp_vars
        self.recompile()
        self.bp_vars = self.bp.NewVariables

    def set_parent(self, clz):
        self.bp.ParentClass = clz
        self.recompile()

    def debug(self):
        LoggingUtil.log("=== Blueprint Function Graphs ===")
        for func in self.bp.FunctionGraphs:
            LoggingUtil.header(f"{func.get_name()} [{func.get_class().get_full_name()}]")
            entry = get_function_entry(func)

            LoggingUtil.header(f"{entry.get_name()} [{entry.get_class().get_full_name()}]")
            for pin in entry.node_pins():
                LoggingUtil.log(f"- [{get_pin_type_str(pin)}] {pin.name}")

            LoggingUtil.undent()

            output = get_function_return(func)
            if output is not None:
                LoggingUtil.header(f"{output.get_name()} [{output.get_class().get_full_name()}]")
                for pin in output.node_pins():
                    LoggingUtil.log(f"- [{get_pin_type_str(pin)}] {pin.name}")
                LoggingUtil.undent()

            LoggingUtil.undent()
        LoggingUtil.log("===")

        LoggingUtil.log("=== Blueprint Event Graphs ===")
        for page in self.bp.UbergraphPages:
            LoggingUtil.header(f"{page.get_name()} [{page.get_class().get_full_name()}]")
            for node in get_event_nodes(page):
                LoggingUtil.header(f"{node.get_name()} ({node.CustomFunctionName}) [{node.get_class().get_full_name()}]")
                for pin in node.node_pins():
                    LoggingUtil.log(f"- [{get_pin_type_str(pin)}] {pin.name}")
                LoggingUtil.undent()
            LoggingUtil.undent()
        LoggingUtil.log("===")

        LoggingUtil.log("=== Blueprint Variables ===")
        for varInfo in self.bp.NewVariables:
            LoggingUtil.header(f"{varInfo.VarName} [{varInfo.VarType.as_dict()}]")
            LoggingUtil.undent()
        LoggingUtil.log("===")

    def add_function(self, node):
        graph = ue.blueprint_add_function(self.bp, node["Name"])
        root = graph.Nodes[0]

        funcFlags = UETools.FunctionFlags(node["FunctionFlags"])

        if UETools.FunctionFlags.FUNC_HasOutParms in funcFlags:
            output = graph.graph_add_node(K2Node_FunctionResult, 300, 0)

        root.ExtraFlags = funcFlags

        for prop in node.get("ChildProperties", []):
            flags = UETools.PropertyFlags(prop.get("PropertyFlags", 0))

            if UETools.PropertyFlags.CPF_Parm in flags:
                target = output if UETools.PropertyFlags.CPF_OutParm in flags else root
                direction = EEdGraphPinDirection.EGPD_Output if UETools.PropertyFlags.CPF_OutParm in flags else EEdGraphPinDirection.EGPD_Input
                target.node_create_pin(direction, UETools.create_pin_type(prop), prop["Name"])

    def add_event(self, node):
        # Ignore Overrides
        if "SuperStruct" in node: return

        graph = self.bp.UberGraphPages[0]
        x, y = graph.graph_get_good_place_for_new_node()
        root = graph.graph_add_node_custom_event(node["Name"], x, y)

        for prop in node.get("ChildProperties", []):
            flags = UETools.PropertyFlags(prop.get("PropertyFlags", 0))
            if UETools.PropertyFlags.CPF_Parm in flags:
                root.node_create_pin(
                    EEdGraphPinDirection.EGPD_Input,
                    UETools.create_pin_type(prop),
                    prop["Name"]
                )


    # An event delegate is just a function but in its own graph in "DelegateSignatureGraphs"
    def add_event_delegate(self, node):
        graph = ue.blueprint_add_event_dispatcher(self.bp, node["Name"][:-len("__DelegateSignature")])
        root = graph.Nodes[0]
        
        root.FunctionFlags = UETools.FunctionFlags(node["FunctionFlags"])

        for prop in node.get("ChildProperties", []):
            flags = UETools.PropertyFlags(prop.get("PropertyFlags", 0))

            if UETools.PropertyFlags.CPF_Parm in flags:
                root.node_create_pin(EEdGraphPinDirection.EGPD_Input, UETools.create_pin_type(prop), prop["Name"])

    def add_var(self, var):
        if var.get("Name") in ["DefaultSceneRoot", "UberGraphFrame"]: return
        if var.get("Type") in ["MulticastInlineDelegateProperty"]: return
        if self.is_var_component(var.get("Name")): return
        varType = UETools.create_pin_type(var)
        self.bp_vars.append(BPVariableDescription(
            VarName=var["Name"],
            VarType=varType,
            PropertyFlags=UETools.PropertyFlags(var.get("PropertyFlags", 0)),
            ReplicationCondition=0,
            DefaultValue="",
            VarGuid=ue.new_guid()
        ))

    def add_vars(self, variables):
        for var in variables:
            self.add_var(var)
        self.apply_variables()

    def add_components(self):
        for item in self.generated_components:
            ue.add_component_to_blueprint(self.bp, item["Class"], item["VarName"])


    def load_defaults(self):
        generated_class = self.bp.GeneratedClass
        self.default_object = ue.load_object(
            generated_class,
            self.path + ".Default__" + generated_class.get_name()
        )

    def set_default_value(self, key, json_value):
        if self.default_object is None: return True
        if key == "UberGraphFrame": return True
        if self.is_real_var_parent_component(key): return True
        if key not in self.default_object.properties():
            LoggingUtil.log(f"ERROR: No matching key ({key}) in default")
            return True

        return UETools.set_property(self.default_object, key, json_value)

    def get_components_node_names(self):
        names = []
        for node in self.generated_components:
            names.append(node["RealName"])
        for node in self.parent_components:
            names.append(node["VarName"])
        return names

    def get_generated_component(self, name : str):
        for cmp in ue.get_blueprint_components(self.bp):
            if cmp.get_name() == name: return cmp
        return None
    
    def get_component_by_node_name(self, name : str):
        cmp = self.get_generated_component(name)
        if cmp is not None: return cmp
        for cmp in self.parent_components:
            if cmp["VarName"] == name: return self.default_object.get_property(cmp["RealName"])
        return None

    def set_component_properties(self, name : str, props):
        if props is None or len(props) == 0: return
        cmp = self.get_component_by_node_name(name)
        if cmp is None: return
        for key, value in props.items():
            UETools.set_property(cmp, key, value)

    def save_defaults(self):
        if self.default_object is None: return
        self.default_object.save_package()