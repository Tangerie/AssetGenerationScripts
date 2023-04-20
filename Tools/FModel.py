from typing import List
import json

class FModelJson:
    __nodes : list

    def __init__(self, path : str):
        with open(path, "r+") as fp:
            self.__nodes = json.load(fp)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.get_by_name(key)
        if callable(key):
            return self.filter(key)
        return self.__nodes[key]
    
    def __getattr__(self, key):
        return self[key]
    
    def get_all_of_key(self, key : str, value):
        return self.filter(lambda node: node.get(key, None) == value)
    
    def get_first_of_key(self, key : str, value):
        for node in self.__nodes:
            if node.get(key, None) == value:
                return node
            
    def get_by_name(self, name : str): self.get_first_of_key("Name", name)

    def nodes(self): return self.__nodes

    def filter(self, func): 
        return tuple(x for x in self.__nodes if func(x))

# Is a dictionary { key: value } or { "key": ..., "value": ... }
def is_dictionary_simple(items : List[dict]):
    if len(items) == 0: return True
    return len(items[0]) == 1

def normalize_dictionary(json_value : List[dict]) -> List[dict]:
    if len(json_value) == 0: return json_value
    if is_dictionary_simple(json_value):
        return [
            {
                "Key": list(item.keys())[0],
                "Value": list(item.values())[0],
            } for item in json_value
        ]
    else:
        return json_value