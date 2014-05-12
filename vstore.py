class VariableStore(dict):
    def __init__(self):
        self.bindings = dict()
        
    def __setitem__(self, key, value):
        print("setting: ", key, value)
        super(VariableStore, self).__setitem__(key, value)
        try:
            for binding in self.bindings[key]:
                binding(key, value)
        except KeyError:
            pass
            
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
            
    def clear(self):
        super(VariableStore, self).clear()
        self.bindings.clear()
        
    def add_binding(self, key, binding):
        try:
            self.bindings[key].append(binding)
        except KeyError:
            self.bindings[key] = [binding]

instance = VariableStore()