import unreal_engine as ue
from unreal_engine.classes import BlueprintFactory, Blueprint, K2Node_FunctionResult, K2Node_Event, K2Node_CustomEvent
from unreal_engine.structs import EdGraphPinType, BPVariableDescription, EdGraphTerminalType
from unreal_engine.enums import EEdGraphPinDirection, EPinContainerType

import Tools.UE as UETools
import Tools.FModel

import LoggingUtil

class BPGenerator():
    path = ""
    bp : Blueprint = None
    default_object = None
    bp_vars = []
    components = {}

    fmodel : Tools.FModel.FModelJson

    def __init__(self, path : str, fmodel : Tools.FModel.FModelJson):
        self.fmodel = fmodel
        self.path = path
        try:
            self.bp = ue.load_object(Blueprint, path)
        except:
            self.bp = BlueprintFactory().factory_create_new(path)

        self.__load_components()
        self.modify()

    def __load_components(self):
        for node in self.fmodel[lambda node: node.get("Type").endswith("Component") and "Class" in node]:
            name = node["Name"]
            isGenerated = name.endswith("_GEN_VARIABLE")
            if isGenerated:
                name = name[:-len("_GEN_VARIABLE")]
            self.components[name] = {
                "gen": isGenerated,
                "class": UETools.find_object(node.get("Class"))
            }

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

        self.compile()
        self.modify()

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
        # LoggingUtil.header(f'[FUNCTION] {node["Name"]}')
        graph = ue.blueprint_add_function(self.bp, node["Name"])
        root = graph.Nodes[0]

        funcFlags = UETools.FunctionFlags(node["FunctionFlags"])

        if UETools.FunctionFlags.FUNC_HasOutParms in funcFlags:
            output = graph.graph_add_node(K2Node_FunctionResult, 300, 0)

        # LoggingUtil.log(funcFlags)
        root.ExtraFlags = funcFlags

        for prop in node.get("ChildProperties", []):
            flags = UETools.PropertyFlags(prop.get("PropertyFlags", 0))

            if UETools.PropertyFlags.CPF_Parm in flags:
                target = output if UETools.PropertyFlags.CPF_OutParm in flags else root
                direction = EEdGraphPinDirection.EGPD_Output if UETools.PropertyFlags.CPF_OutParm in flags else EEdGraphPinDirection.EGPD_Input
                target.node_create_pin(direction, UETools.create_pin_type(prop), prop["Name"])
        # LoggingUtil.undent()

    def add_event(self, node):
        # Ignore Overrides
        if "SuperStruct" in node: return
        LoggingUtil.header(f'[EVENT] {node["Name"]}')

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

        LoggingUtil.undent()

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
        if var.get("Name") in self.components.keys(): return
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
        for name, cmpInfo in self.components.items():
            if not cmpInfo["gen"]: continue
            if name == "DefaultSceneRoot": continue
            ue.add_component_to_blueprint(self.bp, cmpInfo["class"], name)


    def load_defaults(self):
        generated_class = self.bp.GeneratedClass
        self.default_object = ue.load_object(
            generated_class,
            self.path + ".Default__" + generated_class.get_name()
        )

    def set_default_value(self, key, value):
        if self.default_object is None: return
        if key not in self.default_object.properties():
            print(f"ERROR: No matching key ({key}) in default")
            return
        if key == "UberGraphFrame": return
        
        self.default_object.set_property(key, value)

    def save_defaults(self):
        if self.default_object is None: return
        self.default_object.save_package()