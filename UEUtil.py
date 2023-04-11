import inspect

def get_class_by_path(path):
    import unreal_engine as ue
    try:
        return ue.find_class(path)
    except:
        try:
            return ue.find_object(path)
        except:
            return None

import unreal_engine as ue

STRUCT_MAP = {
    ue.FVector2D: get_class_by_path("Vector2D"),
    ue.FLinearColor: get_class_by_path("LinearColor")
}


        
def create_struct_from_dict(struct, props):
    struct = STRUCT_MAP.get(struct, struct)
    kwargs = {}
    print(struct)
    structKeys = struct.properties()
    structDict = struct.as_dict()
    for key in structKeys:
        if key not in props: continue
        valueTy = STRUCT_MAP.get(type(structDict[key]), type(structDict[key]))

        if valueTy == ue.UScriptStruct:
            kwargs[key] = create_struct_from_dict(valueTy.get_struct(), props[key])
            print(f"STRUCT [{key}]")
            

    return struct(**kwargs)

KEYS_TO_IGNORE = ["ColorTag", "Font"]

def set_properties_by_json(obj, props, to_ignore = []):
    import unreal_engine as ue

    for key in obj.properties():
        if key not in props or key in to_ignore or key in KEYS_TO_IGNORE: continue
        jsonValue = props[key]
        prevValue = getattr(obj, key)
        prevValueType = type(prevValue)
        
        if prevValueType == ue.UScriptStruct:
            print(f"{key}")
            newValue = create_struct_from_dict(prevValue.get_struct(), jsonValue)
            setattr(obj, key, newValue)
