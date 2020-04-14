import copy

class Scope():
    def __init__(self):
        self.in_function = None # Are we currently inside of a function body? What function object?
        self.nr_instructions_in_func = 0 # How many lines have been written in the current function?
        self.indent = 0
        self.vars = {
            "int": {
                "num_created": 0,
                "available": []
            },
            "bool": {
                "num_created": 0,
                "available": []
            },
        }
        self.avars = {
            "int": {
                "num_created": 0,
                "available": []
            },
            "bool": {
                "num_created": 0,
                "available": []
            },
        }
        self.funcs = {
            "num_created": 0,
            "available": []
        }

    def reduce_indentation(self):
        """
        Reduce indentation level and remove vars/avars/funcs that go out of scope.
        """
        if self.indent == 0:
            raise Exception("Code: Trying to reduce indentation below 0")
        
        self.indent -= 1
        
        for type, obj in self.vars.items():
            vars_still_in_scope = []
            for var in obj['available']:
                if var.indent <= self.indent:
                    vars_still_in_scope.append(var)

            self.vars[type]['available'] = vars_still_in_scope

        for type, obj in self.avars.items():
            avars_still_in_scope = []
            for var in obj['available']:
                if var.indent <= self.indent:
                    vars_still_in_scope.append(var)

            self.avars[type]['available'] = avars_still_in_scope

        funcs_still_in_scope = []
        for func in self.funcs['available']:
            if func.indent <= self.indent:
                funcs_still_in_scope.append(func)

        self.funcs['available'] = funcs_still_in_scope


    def clone(self):
        """
        Return a new Sope object with identical member values as self.
        """
        clone = Scope()
        clone.in_function = self.in_function
        clone.nr_instructions_in_func = self.nr_instructions_in_func
        clone.indent = self.indent
        clone.vars = copy.deepcopy(self.vars)
        clone.avars = copy.deepcopy(self.avars)
        clone.funcs = copy.deepcopy(self.funcs)