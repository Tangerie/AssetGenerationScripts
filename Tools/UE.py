from typing import Callable, Dict
import unreal_engine as ue
from unreal_engine.classes import K2Node_FunctionResult, K2Node_Event, K2Node_CustomEvent
from unreal_engine.structs import EdGraphPinType, EdGraphTerminalType
from unreal_engine.enums import EPinContainerType

from enum import IntFlag
import json
import LoggingUtil

import Tools.FModel as FTools

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



# FOR Non-Objects ONLY
# fprop.get_inner().convert()
# fprop.get_type_str()

# bp.default_object.get_property("ComboSplitData").SplitFrame = 2
# fprop = bp.default_object.get_fproperty("ComboAnimationTags")
# print(fprop.get_inner().convert())
# print(fprop.get_type_str())


'''
=== ALL TYPE STRINGS ===
[X] BoolProperty
[X] IntProperty
[X] UInt32Property
[X] Int32Property
[X] Int64Property
[X] UInt64Property
[X] FloatProperty
[X] DoubleProperty
[X] ByteProperty
[X] EnumProperty
[X] StrProperty
[X] TextProperty
[X] NameProperty
[X] ObjectProperty
[ ] ClassProperty

[X] FVector
[X] FVector2D
[X] FRotator
[X] FTransform
[X] FQuat
[X] FColor
[X] FLinearColor
[X] FHitResult

[X] UScriptStruct
[X] StructProperty

[ ] WeakObjectProperty
[ ] MulticastDelegateProperty
[ ] DelegateProperty

[X] ArrayProperty
[X] MapProperty
[X] SetProperty
'''

# Types that are just set as their JSON value
SIMPLE_TYPES = (
    "BoolProperty",
    "IntProperty",
    "UInt32Property",
    "Int32Property",
    "UInt64Property",
    "Int64Property",
    "FloatProperty",
    "DoubleProperty",
    "StrProperty",
    "NameProperty"
)


BASE_STRUCT_CONSTRUCTORS : Dict[str, Callable[[dict], tuple]] = {
    "FVector": lambda v: (v["X"], v["Y"], v["Z"]),
    "FVector2D": lambda v: (v["X"], v["Y"]),
    "FRotator": lambda v: (v["Roll"], v["Pitch"], v["Yaw"]),
    "FTransform": lambda v: (
        create_base_struct("FVector", v["Translation"]),
        create_base_struct("FQuat", v["Rotation"]),
        create_base_struct("FVector", v["Scale3D"])
    ),
    "FQuat": lambda v: (v["X"], v["Y"], v["Z"], v["W"]),
    "FColor": lambda v: (v["R"], v["G"], v["B"], v["A"]),
    "FLinearColor": lambda v: (v["R"], v["G"], v["B"], v["A"]),
    "FHitResult": lambda v: tuple() # No Init for FHitResult (Not editable in editor anyway)
}

SAFE_CREATE_TYPES = (
    *SIMPLE_TYPES, 
    *BASE_STRUCT_CONSTRUCTORS.keys(), 
    "ByteProperty",
    "TextProperty",
    "ObjectProperty",
    "EnumProperty"
)

def is_type_safe_to_create(typeStr): return typeStr in SAFE_CREATE_TYPES

def create_base_struct(structName, json_value):
    if structName in BASE_STRUCT_CONSTRUCTORS:
        args = BASE_STRUCT_CONSTRUCTORS[structName](json_value)
        return getattr(ue, structName)(*args)

def get_inner_type(typeStr : str):
    inside = typeStr.split("<")[-1][:-1]
    if "," in inside:
        return inside.split(",")
    else:
        return inside

# Only UScriptStructs cannot be created/set this way
def create_from_type_str(baseType, json_value):
    if baseType in SIMPLE_TYPES:
        return json_value
    elif baseType in BASE_STRUCT_CONSTRUCTORS:
        v = create_base_struct(baseType, json_value)
        if v is not None:
            return v
        return None # Is this ok?
    elif baseType == "ByteProperty" and isinstance(json_value, int):
        return json_value
    elif baseType == "TextProperty":
        # TODO Set localization property
        if "CultureInvariantString" in json_value:
            return json_value["CultureInvariantString"]
        else:
            return json_value["SourceString"]
    elif baseType == "ObjectProperty":
        if json_value is None: return None
        elif isinstance(json_value, str):
            return find_object(json_value)
        elif "ObjectName" in json_value:
            return find_object(json_value)
        elif "AssetPathName" in json_value:
            return find_object(json_value["AssetPathName"])
        else:
            return None
    elif baseType == "EnumProperty":
        if isinstance(json_value, str) and "::" in json_value:
            enumClassName, enumValue = json_value.split("::")
            enumClass = find_object(enumClassName)
            if enumClass is None:
                LoggingUtil.log("Failed to find enum")
                return 0
            else:
                if enumValue in enumClass.enum_names():
                    index = enumClass.enum_names().index(enumValue)
                else: index = 0
                return index
        else:
            LoggingUtil.log("Unknown Enum Value")
            return 0
        
def set_struct_from_dict(struct, json_value):
    struct_type = struct.get_struct().get_name()
    # FModel seralizes this one weird, need to convert to proper format
    if struct_type == "GameplayTagContainer": 
        json_value = {
            "GameplayTags": [
                {
                    "TagName": x
                } for x in json_value
            ],
        }
    for field_name in struct.fields():
        if field_name in json_value:
            set_property(struct, field_name, json_value.get(field_name))


def set_property(obj, key : str, json_value):
    isStruct = isinstance(obj, ue.UScriptStruct)
    if isStruct:
        set_p = obj.set_field
        get_p = obj.get_field
    else:
        set_p = obj.set_property
        get_p = obj.get_property

    fprop = obj.get_fproperty(key)
    typeStr = fprop.get_type_str()
    baseType = typeStr.split("<")[0]

    LoggingUtil.header(f"{key} [{typeStr}]")

    wasSet = True
    if is_type_safe_to_create(baseType):
        v = create_from_type_str(baseType, json_value)
        if v is not None and baseType != "ObjectProperty":
            set_p(key, v)
    elif baseType == "UScriptStruct":
        struct = get_p(key)
        set_struct_from_dict(struct, json_value)
    elif baseType == "ArrayProperty":
        innerType = get_inner_type(typeStr)
        if is_type_safe_to_create(innerType):
            set_p(key, [
                create_from_type_str(innerType, x) for x in json_value
            ])
        elif innerType == "UScriptStruct":
            if json_value is not None:
                fprop.set_length(obj, len(json_value))
                for i, v in enumerate(json_value):
                    set_struct_from_dict(fprop.get_at_index(obj, i), v)
        else:
            LoggingUtil.log("Unknown Inner Type")
            wasSet = False
    elif baseType == "SetProperty":
        innerType = get_inner_type(typeStr)
        if is_type_safe_to_create(innerType):
            set_p(key, set(
                create_from_type_str(innerType, x) for x in json_value
            ))
        else:
            LoggingUtil.log("Unknown Inner Type")
            wasSet = False
    elif baseType == "MapProperty":
        innerKeyType, innerValueType = get_inner_type(typeStr)
        if json_value is None: json_value = []
        fixed_dict = FTools.normalize_dictionary(json_value)

        if is_type_safe_to_create(innerValueType):
            for item in fixed_dict:
                fprop.add_key_value(
                    obj, 
                    create_from_type_str(innerKeyType, item["Key"]),
                    create_from_type_str(innerValueType, item["Value"])
                )
        elif innerValueType == "UScriptStruct": 
            for item in fixed_dict:
                struct = fprop.add_key(obj, create_from_type_str(innerKeyType, item["Key"]))
                set_struct_from_dict(struct, item["Value"])
        else:
            wasSet = False
    else:
        LoggingUtil.log("UNHANDELLED")
        wasSet = False
        
    LoggingUtil.undent()
    return wasSet


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

OBJECT_CACHE = {}

def find_object(objRef):
    global OBJECT_CACHE
    obj = None

    if isinstance(objRef, dict):
        if "ObjectName" in objRef and "ObjectPath" in objRef:
            _basePath = objRef["ObjectPath"].split(".")[0]
            _assetName = objRef["ObjectName"].split("'")[1]
            _assetType = objRef["ObjectName"].split("'")[0]
            name = f"{_basePath}.{_assetName}"
            try:
                ue.load_object(ue.find_class(_assetType), name)
            except:
                pass
        else:
            name = objRef["ObjectName"]
    else:
        name = objRef

    if name in OBJECT_CACHE:
        return OBJECT_CACHE[name]
    

    try:
        obj = ue.find_object(name)
    except:
        pass

    if obj is None:
        try:
            ue.load_object(name)
            obj = ue.find_object(name)
        except:
            pass
    
    if obj is None:
        LoggingUtil.log(f"Failed to find {name}")
        return None

    OBJECT_CACHE[name] = obj
    return obj

def resolve_property_type(props):
    kwargs = {}

    if props["Type"].endswith("Property"):
        kwargs["Type"] = props["Type"][:-len("Property")].lower()

    if props["Type"] == "ObjectProperty":
        kwargs["Ref"] = find_object(props["PropertyClass"])
    elif props["Type"] == "ClassProperty":
        kwargs["Ref"] = find_object(props["MetaClass"])
    elif props["Type"] == "SoftObjectProperty":
        kwargs["Ref"] = find_object(props["PropertyClass"])
    elif props["Type"] == "SoftClassProperty":
        kwargs["Ref"] = find_object(props["MetaClass"])
    elif props["Type"] == "StructProperty":
        kwargs["Ref"] = find_object(props["Struct"])
    elif props["Type"] == "ByteProperty" and props.get("Enum", None) is not None:
        kwargs["Ref"] = find_object(props["Enum"])
    elif props["Type"] == "EnumProperty":
        kwargs["Type"] = "byte"
        kwargs["Ref"] = find_object(props["Enum"])
    elif props["Type"] == "StrProperty":
        kwargs["Type"] = "String"
    elif props["Type"] == "InterfaceProperty":
        kwargs["Type"] = "interface"
        kwargs["Ref"] = find_object(props["InterfaceClass"])

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