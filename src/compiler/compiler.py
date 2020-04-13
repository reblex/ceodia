import re

class Compiler():
    """
    Compile from Statically Typed Psuedo-Python to Python3
    """

    def __init__(self):
        pass

    def compile(self, code):
        """
        Compile a pre-compiled Code Object to Python3 code. 
        Return a list of strings representing correctly indented Python3 code.
        """
        compiled_lines = []

        for instruction in code.written_instructions:
            compiled_elements = []
            compiled_line = ""

            # Set the indentation
            for _ in range(instruction.indent):
                compiled_line += "\t"

            # Compile each element of the instruction
            for element in instruction.pre_compiled_elements:
                if element != "nlb":
                    compiled_elements.append(self.compile_element(element))

            # Make the line a string
            compiled_line += " ".join(compiled_elements)
            compiled_lines.append(compiled_line)

        return compiled_lines

    def compile_element(self, element):
        """
        Compile and instruction element.
        """
        e = element
        if e.startswith("nvar") or e.startswith("pvar") or e.startswith("var") or e.startswith("avar"):
            return self.compile_var_name(e)
        
        elif e.startswith("nfunc") or e.startswith("func"):
            return self.compile_func(e)

        else:
            return e


    def compile_func(self, element):
        """
        Create a valid python3 function defenition/call based on a func element.
        Ex 1: nfunc<int>0(pvar<int>0,pvar<bool>0) => func0_int(arg_int0, arg_bool0)
        Ex 2: func<void>3() => func0_void()
        """
        params = re.findall(r"[pa]*var<.*?>\d+", element)
        return_type = re.findall(r"func<(.*?)>", element)[0]
        number = re.findall(r">([\d]+?)\(", element)[0]

        compiled_params = []
        for param in params:
            compiled_params.append(self.compile_var_name(param))

        name = "func_" + return_type + number

        param_list = "(" + ", ".join(compiled_params) + ")"

        return name + param_list


    def compile_var_name(self, element):
        """
        Create a valid python3 variable name based on a variable element.
        Ex 1: nvar<int>1 => int1
        Ex 2: pvar<bool>3 => arg_bool3
        """
        type = re.findall(r"<(.*?)>", element)[0]
        number = re.findall(r">([\d]+)", element)[0]

        name = ""

        if element.startswith("p") or element.startswith("a"):
            name += "arg_"

        name += type + number

        return name