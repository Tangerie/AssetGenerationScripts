class FModelJson:
    __nodes : list

    def __init__(self, path : str):
        import json

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