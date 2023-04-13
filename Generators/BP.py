import unreal_engine as ue
from unreal_engine.classes import BlueprintFactory, Blueprint, K2Node_FunctionResult, K2Node_Event, K2Node_CustomEvent
from unreal_engine.structs import EdGraphPinType, BPVariableDescription, EdGraphTerminalType
from unreal_engine.enums import EEdGraphPinDirection, EPinContainerType

from enum import IntFlag
import json

import LoggingUtil

class PropertyFlags(IntFlag):
    CPF_None                              = 0x0,
    CPF_Edit                              = 0x0000000000000001,
    CPF_ConstParm                         = 0x0000000000000002,
    CPF_BlueprintVisible                  = 0x0000000000000004,
    CPF_ExportObject                      = 0x0000000000000008,
    CPF_BlueprintReadOnly                 = 0x0000000000000010,
    CPF_Net                               = 0x0000000000000020,
    CPF_EditFixedSize                     = 0x0000000000000040,
    CPF_Parm                              = 0x0000000000000080,
    CPF_OutParm                           = 0x0000000000000100,
    CPF_ZeroConstructor                   = 0x0000000000000200,
    CPF_ReturnParm                        = 0x0000000000000400,
    CPF_DisableEditOnTemplate             = 0x0000000000000800,
    CPF_Transient                         = 0x0000000000002000,
    CPF_Config                            = 0x0000000000004000,
    CPF_DisableEditOnInstance             = 0x0000000000010000,
    CPF_EditConst                         = 0x0000000000020000,
    CPF_GlobalConfig                      = 0x0000000000040000,
    CPF_InstancedReference                = 0x0000000000080000,
    CPF_DuplicateTransient                = 0x0000000000200000,
    CPF_SaveGame                          = 0x0000000001000000,
    CPF_NoClear                           = 0x0000000002000000,
    CPF_ReferenceParm                     = 0x0000000008000000,
    CPF_BlueprintAssignable               = 0x0000000010000000,
    CPF_Deprecated                        = 0x0000000020000000,
    CPF_IsPlainOldData                    = 0x0000000040000000,
    CPF_RepSkip                           = 0x0000000080000000,
    CPF_RepNotify                         = 0x0000000100000000,
    CPF_Interp                            = 0x0000000200000000,
    CPF_NonTransactional                  = 0x0000000400000000,
    CPF_EditorOnly                        = 0x0000000800000000,
    CPF_NoDestructor                      = 0x0000001000000000,
    CPF_AutoWeak                          = 0x0000004000000000,
    CPF_ContainsInstancedReference        = 0x0000008000000000,
    CPF_AssetRegistrySearchable           = 0x0000010000000000,
    CPF_SimpleDisplay                     = 0x0000020000000000,
    CPF_AdvancedDisplay                   = 0x0000040000000000,
    CPF_Protected                         = 0x0000080000000000,
    CPF_BlueprintCallable                 = 0x0000100000000000,
    CPF_BlueprintAuthorityOnly            = 0x0000200000000000,
    CPF_TextExportTransient               = 0x0000400000000000,
    CPF_NonPIEDuplicateTransient          = 0x0000800000000000,
    CPF_ExposeOnSpawn                     = 0x0001000000000000,
    CPF_PersistentInstance                = 0x0002000000000000,
    CPF_UObjectWrapper                    = 0x0004000000000000,
    CPF_HasGetValueTypeHash               = 0x0008000000000000,
    CPF_NativeAccessSpecifierPublic       = 0x0010000000000000,
    CPF_NativeAccessSpecifierProtected    = 0x0020000000000000,
    CPF_NativeAccessSpecifierPrivate      = 0x0040000000000000,
    CPF_SkipSerialization                 = 0x0080000000000000,

class FunctionFlags(IntFlag):
    FUNC_None                      = 0x00000000,
    FUNC_Final                     = 0x00000001,
    FUNC_RequiredAPI               = 0x00000002,
    FUNC_BlueprintAuthorityOnly    = 0x00000004,
    FUNC_BlueprintCosmetic         = 0x00000008,
    FUNC_Net                       = 0x00000040,
    FUNC_NetReliable               = 0x00000080,
    FUNC_NetRequest                = 0x00000100,
    FUNC_Exec                      = 0x00000200,
    FUNC_Native                    = 0x00000400,
    FUNC_Event                     = 0x00000800,
    FUNC_NetResponse               = 0x00001000,
    FUNC_Static                    = 0x00002000,
    FUNC_NetMulticast              = 0x00004000,
    FUNC_UbergraphFunction         = 0x00008000,
    FUNC_MulticastDelegate         = 0x00010000,
    FUNC_Public                    = 0x00020000,
    FUNC_Private                   = 0x00040000,
    FUNC_Protected                 = 0x00080000,
    FUNC_Delegate                  = 0x00100000,
    FUNC_NetServer                 = 0x00200000,
    FUNC_HasOutParms               = 0x00400000,
    FUNC_HasDefaults               = 0x00800000,
    FUNC_NetClient                 = 0x01000000,
    FUNC_DLLImport                 = 0x02000000,
    FUNC_BlueprintCallable         = 0x04000000,
    FUNC_BlueprintEvent            = 0x08000000,
    FUNC_BlueprintPure             = 0x10000000,
    FUNC_EditorOnly                = 0x20000000,
    FUNC_Const                     = 0x40000000,
    FUNC_NetValidate               = 0x80000000,
    FUNC_AllFlags                  = 0xFFFFFFFF,

def get_pin_type_str(pin):
    v = str(pin)[len("<unreal_engine.EdGraphPin "):-1]
    return json.loads(v.replace("'", '"'))['type']

def get_function_entry(func):
    for node in func.Nodes:
        if node.get_class() == ue.find_class("/Script/BlueprintGraph.K2Node_FunctionEntry"):
            return node

def get_function_return(func):
    for node in func.Nodes:
        if node.get_class() == K2Node_FunctionResult:
            return node

def find_object(name):
    try:
        return ue.find_object(name)
    except:
        return None


def resolve_property_type(props):
    kwargs = {}

    if props["Type"].endswith("Property"):
        kwargs["Type"] = props["Type"][:-len("Property")].lower()

    if props["Type"] == "ObjectProperty":
        kwargs["Ref"] = find_object(props["PropertyClass"]["ObjectName"])
    elif props["Type"] == "StructProperty":
        kwargs["Ref"] = find_object(props["Struct"]["ObjectName"])
    elif props["Type"] == "ByteProperty" and "Enum" in props:
        kwargs["Ref"] = find_object(props["Enum"]["ObjectName"])

    return kwargs

def create_pin_type(props):
    kwargs = {}

    if props["Type"] == "ArrayProperty":
        props = props["Inner"]
        kwargs["ContainerType"] = EPinContainerType.Array
    elif props["Type"] == "MapProperty":
        kwargs["ContainerType"] = EPinContainerType.Map
        valueRes = resolve_property_type(props["ValueProp"])

        valueKwargs = {
            "TerminalCategory": valueRes["Type"]
        }

        if "Ref" in valueRes:
            valueKwargs["TerminalSubCategoryObject"] = valueRes["Ref"]

        kwargs["PinValueType"] = EdGraphTerminalType(**valueKwargs)

        props = props["KeyProp"]
    elif props["Type"] == "SetProperty":
        props = props["ElementProp"]
        kwargs["ContainerType"] = EPinContainerType.Set

    res = resolve_property_type(props)
    kwargs["PinCategory"] = res["Type"]

    if "Ref" in res:
        kwargs["PinSubCategoryObject"] = res["Ref"]

    return EdGraphPinType(**kwargs)

def get_event_nodes(graph):
    return tuple(x for x in graph.Nodes if x.get_class() in (K2Node_Event, K2Node_CustomEvent))

class BPGenerator():
    path = ""
    bp : Blueprint = None

    def __init__(self, path : str):
        try:
            self.bp = ue.load_object(Blueprint, path)
        except:
            self.bp = BlueprintFactory().factory_create_new(path)

        self.bp.modify()

    def clear(self):
        # Clear all functions
        self.bp.FunctionGraphs = [
            func for func in self.bp.FunctionGraphs if func.get_name() == "UserConstructionScript"
        ]

        # Clear EventGraph
        self.bp.UbergraphPages = [
            page for page in self.bp.UbergraphPages if page.get_name() == "EventGraph"
        ]

        for node in self.bp.UberGraphPages[0].Nodes:
            self.bp.UberGraphPages[0].graph_remove_node(node)

        # self.bp.NewVariables = []

    def compile(self):
        ue.blueprint_mark_as_structurally_modified(self.bp)
        self.bp.post_edit_change()
        ue.compile_blueprint(self.bp)

    def set_parent(self, clz):
        self.bp.ParentClass = clz

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

        funcFlags = FunctionFlags(node["FunctionFlags"])

        if FunctionFlags.FUNC_HasOutParms in funcFlags:
            output = graph.graph_add_node(K2Node_FunctionResult, 300, 0)

        # LoggingUtil.log(funcFlags)
        root.ExtraFlags = funcFlags

        for prop in node.get("ChildProperties", []):
            flags = PropertyFlags(prop.get("PropertyFlags", 0))

            if PropertyFlags.CPF_Parm in flags:
                target = output if PropertyFlags.CPF_OutParm in flags else root
                direction = EEdGraphPinDirection.EGPD_Output if PropertyFlags.CPF_OutParm in flags else EEdGraphPinDirection.EGPD_Input
                target.node_create_pin(direction, create_pin_type(prop), prop["Name"])
        # LoggingUtil.undent()

    def add_event(self, node):
        # Ignore Overrides
        if "SuperStruct" in node: return
        LoggingUtil.header(f'[EVENT] {node["Name"]}')

        graph = self.bp.UberGraphPages[0]
        x, y = graph.graph_get_good_place_for_new_node()
        root = graph.graph_add_node_custom_event(node["Name"], x, y)

        for prop in node.get("ChildProperties", []):
            flags = PropertyFlags(prop.get("PropertyFlags", 0))
            if PropertyFlags.CPF_Parm in flags:
                root.node_create_pin(
                    EEdGraphPinDirection.EGPD_Input,
                    create_pin_type(prop),
                    prop["Name"]
                )

        LoggingUtil.undent()

    def add_vars(self, variables):
        newVars = []
        for var in variables:
            if var["Name"] == "UberGraphFrame": continue
            varType = create_pin_type(var)
            newVars.append(BPVariableDescription(
                VarName=var["Name"],
                VarType=varType,
                PropertyFlags=PropertyFlags(var.get("PropertyFlags", 0))
            ))
        self.bp.NewVariables = newVars 