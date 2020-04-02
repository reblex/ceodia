class Variable():
    """docstring for Variable."""
    def __init__(self, type, indent, number, is_argument=False):
        self.type = type
        self.indent = indent
        self.number = number
        self.idx_of = None
        self.is_argument = is_argument
        
    def __str__(self):
        """
        Return the tokenized version of the variable.
        """
        token = ""
        if self.is_argument:
            token += "avar"
        else:
            token += "var"

        token += "<" + str(self.type) + ">" + str(self.number)

        return token