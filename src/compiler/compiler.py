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
        compiled_lines = ["#!/usr/bin/env python3"]

        for i, instruction in enumerate(code.written_instructions):
            
            # Don't print multiple newlines for NLB.
            if i > 1:
                if instruction.template[0] == "nlb":
                    if code.written_instructions[i-1].template[0] == "nlb":
                        continue
                    else:
                        compiled_lines.append("")
                        continue

            # Vertical spacing.
            if instruction.is_statement() or instruction.template[0] == "return":
                if i > 1:
                    prev_instr = code.written_instructions[i-1]
                    if not prev_instr.is_statement() and prev_instr.template[0] != "nlb":
                        compiled_lines.append("")
            
            compiled_elements = []
            compiled_line = ""

            # Set the indentation
            for _ in range(instruction.indent):
                compiled_line += "\t"

            # Compile each element of the instruction
            for element in instruction.pre_compiled_elements:
                compiled_elements.append(self.compile_element(element))

            # Make the line a string
            compiled_line += " ".join(compiled_elements)
            
            if instruction.is_statement():
                compiled_line += ":"
            
            compiled_lines.append(compiled_line)

        return compiled_lines


    def compile_and_write(self, code, path):
        """
        Compile code and write to file. Returns compiled code as list of strings if desired.
        """
        compiled_lines = self.compile(code)

        with open(path, "w") as file:
            for line in compiled_lines:
                file.write(line + "\n")

        return compiled_lines

    def compile_element(self, element):
        """
        Compile and instruction element.
        """
        if "{{" not in element:
            if element.startswith("nvar") or element.startswith("pvar") or element.startswith("var"):
                return self.compile_var_name(element)

            # TODO: I think this is redundant, as functions should be wrapped in {{}}.
            elif element.startswith("nfunc") or element.startswith("func"):
                return self.compile_func(element)

            else:
                return element

        # Element contains multiple dynamic parts {{...}}.
        for dynamic_part in [elem for elem in re.findall("{{(.*?)}}", element)]:
            compiled_part = ""
            if dynamic_part.startswith("nvar") or dynamic_part.startswith("pvar") or dynamic_part.startswith("var"):
                compiled_part = self.compile_var_name(dynamic_part)

            elif dynamic_part.startswith("nfunc") or dynamic_part.startswith("func"):
                compiled_part = self.compile_func(dynamic_part)
            
            else:
                compiled_part = dynamic_part

            element = element.replace("{{"+dynamic_part+"}}", compiled_part, 1)

        return element


    def compile_func(self, element):
        """
        Create a valid python3 function defenition/call based on a func element.
        Ex 1: nfunc<int>0(pvar<int>0,pvar<bool>0) => func0_int(arg_int0, arg_bool0)
        Ex 2: func<void>3() => func0_void()
        """
        params = re.findall(r"[p]*var<.*?>\d+", element)
        return_type = re.findall(r"func<(.*?)>", element)[0]
        return_type = return_type.replace("[]", "_list")
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
        var_type = re.findall(r"<(.*?)>", element)[0].replace("[]", "_list")
        number = re.findall(r">([\d]+)", element)[0]

        name = var_type + number

        return name