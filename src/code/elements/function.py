class Function():
    """docstring for Function."""
    def __init__(self, indent, param_types, param_arg_vars, number, return_type):
        self.indent = indent
        self.param_types = param_types         # Ex: [int, int] for func(pvar<int>,pvar<int>)
        self.param_arg_vars = param_arg_vars   # The actual Variable objects representing the arguments.
        self.number = number
        self.return_type = return_type
        self.has_been_defined = False
        self.has_returned = False


    def call(self, args=[]):
        """
        __str__ wrapper for when calling the function.
        """
        return self.__str__(args)


    def __str__(self, args=[]):
        """
        Return the tokenized version of the function.
        args is a list of arguments for when calling a function.
        """
        # TODO: Clean this up, reduce copied code.
        param_str = ""
        if not self.has_been_defined:
            arg_str = ""
            for i, param in enumerate(self.param_arg_vars):
                if i > 0:
                    arg_str += ","
                
                arg_str += "pvar<" + str(param.type) + ">" + str(param.number)
            
            param_str = "nfunc<" + self.return_type + ">" + str(self.number) + "(" + arg_str + ")"
            self.has_been_defined = True

        else:
            arg_str = ",".join([str(var) for var in args])
            param_str = "func<" + self.return_type + ">" + str(self.number) + "(" + arg_str + ")"   

        return param_str