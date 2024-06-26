from src.code.elements.function import Function
from src.code.elements.variable import Variable
from src.code.elements.scope import Scope

import re

class Instruction():
    """Represents one line of Code"""

    def __init__(self, template=None):
        self.template = []                   # List of elemnts in the instruction.
        self.elements = []                   # Uncompiled elements. Mix of static strings & element objects.
        self.indent = None                   # Indentation of the line (amount of tabs)
        self.pre_compiled_elements = []      # All elements after pre-compilation.

        if template != None:
            self.template = template.split(" ")
            self.elements = self.template.copy()


    def is_statement(self):
        """Is this instruction a statement? i.e. does it increase indentation?"""
        if self.template[0] in ["def", "for", "while", "if"]:
            return True
        else:
            return False


    def get_required_elements(self):
        """
        Return all dynamic elements required.
        This only includes elements that already need to be in place
        in the code, such as variables and functions, and not
        static values that just need to be filled in like "<int>" or "<bool>".
        """
        return self.get_dynamic_element_tokens(True)


    def must_be_in_function(self):
        """
        Is the function required to be inside of a function?
        """
        for element in self.template:
            if element == "return":
                return True

        return False


    def get_dynamic_element_tokens(self, only_required=False):
        """
        Return ALL element tokens that are required to be filled out in order to complete the instruction.
        This function also internally marks where those elements appear, which is used when
        completing the instruction.
        """
        dynamic_elements = []
        for element in self.template:
            for sub_element in [elem[2:-2] for elem in re.findall("{{.*?}}", element)]:
                # Dynamic element Values
                if not only_required:
                    if sub_element in ["<int>", "<bool>", "<float>", "<int[]>", "<float[]>"]:
                        dynamic_elements.append(sub_element)
                
                # Variables and functions
                if sub_element.startswith("var") or sub_element.startswith("func"):
                    dynamic_elements.append(sub_element)

        return dynamic_elements


    def precompile(self, args, scope):
        """
        Fill out all dynamic elements of the instruction to complete it. Then update the scope.
        The dynamic elements are represented as a list(args) in order.
        Returns the updated scope.
        """

        # TODO: Something similar to this but without using element indexes? (count nr of {{}}?)
        # Make sure that all dynamic elements are being filled.
        # if len(args) != len(self.dynamic_element_indexes):
        #     raise Exception("Incorrect number of dynamic elements when completing instruction.")

        # Make note if a function has called return.
        if self.elements[0] == "return":
            scope.in_function.has_returned = True

        # Replace dynamic elements with elements given by code_writer.
        replacements_made = 0
        for idx, element in enumerate(self.elements):
            for dynamic_part in [elem for elem in re.findall("{{.*?}}", element)]:
                replacement = ""
                
                if dynamic_part.startswith("{{func"):
                    # A self-created function call replacement is based on a list containing
                    # the function object along with any arguments.
                    replacement = "{{" + args[replacements_made][0].call(args[replacements_made][1:]) + "}}"

                else:
                    replacement = "{{"+str(args[replacements_made])+"}}"

                self.elements[idx] = self.elements[idx].replace(dynamic_part, replacement, 1)
                replacements_made += 1
                print("Replacing", dynamic_part, "with", replacement, "in element", element)
                print("Elements are now:", self.elements)

        # Create variable/func objects, update scope etc.
        # And finally, pre-compile elements into tokens.
        for element in self.elements:
            scope = self.parse_element(element, scope)

        # LASTLY!! Increase indent if this instruction is a statement.
        if self.is_statement():
            scope.indent += 1

        return scope


    def load(self, string, scope):
        """
        Load an instruction from an already pre-compiled instruction string
        and update the scope. Similar to the precompile function.
        """

        self.indent = string.count("\t")
        elements = string.replace("\t", "").replace("\n", "").split(" ")

        self.template = self.recreate_tempalte(elements)

        # Make note if a function has called return.
        if elements[0] == "return":
            scope.in_function.has_returned = True

        # Create variable/func objects, update scope etc.
        for element in elements:
            scope = self.parse_element(element, scope)

        # LASTLY!! Increase indent if this instruction is a statement.
        if self.is_statement():
            scope.indent += 1

        return scope  


    def parse_element(self, element, scope):
        """
        Create variable/func objects, update scope etc.
        And finally, pre-compile elements into tokens.
        """

        # The instruction is just reducing indentation.
        if element == "nlb":
            scope.reduce_indentation()

            # Exiting a function body
            if scope.in_function != None:
                if scope.in_function.indent == scope.indent:
                    scope.in_function = None
                    scope.nr_instructions_in_func = 0
            else:
                scope.nr_instructions_in_func += 1

            self.pre_compiled_elements.append("nlb")

        # The instruction is defining a new function.
        # Create a new function object and argument variables if present.
        elif element.startswith("nfunc"):
            return_type = re.findall(r"nfunc<(.*?)>", element)[0]
            param_types = re.findall(r"pvar<(.*?)>", element)

            # Create the argument variables representing the parameters, if present.
            param_arg_vars = []
            for param_type in param_types:
                # TODO: Move handling of creation of vars/funcs to Scope class?
                var_num = scope.vars[param_type]['num_created']
                scope.vars[param_type]['num_created'] += 1
                
                var = Variable(param_type, scope.indent + 1, var_num, True)
                var.has_been_defined = True
                param_arg_vars.append(var)
                scope.vars[param_type]['available'].append(var)

            # Create the function object.
            func_num = scope.funcs['num_created']
            scope.funcs['num_created'] += 1
            
            func = Function(scope.indent, param_types, param_arg_vars, func_num, return_type)
            scope.funcs['available'].append(func)

            # Entering function body, mark what function it is so we know
            # when we are exiting it.
            scope.in_function = func

            self.pre_compiled_elements.append(str(func))

        # Creation of a variable.
        elif element.startswith("nvar") or element.startswith("pvar"):
            var_type = re.findall(r"<(.*?)>", element)[0]
            var_num = scope.vars[var_type]['num_created']
            scope.vars[var_type]['num_created'] += 1
            
            indent = scope.indent
            is_argument = False
            if element.startswith("pvar"):
                is_argument = True
                indent += 1

            var = Variable(var_type, indent, var_num, is_argument)
            scope.vars[var_type]['available'].append(var)

            self.pre_compiled_elements.append(str(var))

        # Static elements are just appended, as they are already pre-compiled.
        else:
            self.pre_compiled_elements.append(element)


        return scope


    def recreate_tempalte(self, elements):
        """
        Recreate an instruction template from a list of pre-compiled elements.
        This is used to recreate the original template of a loaded instruction.
        """
        parsed_elements = []
        for element in elements:
            parsed_elements.append(self.recreate_template_element(element))
        
        return parsed_elements


    def recreate_template_element(self, element):
        """
        Recreate an instruction element into the original template element.
        """
        if self.is_int(element):
            return "<int>"

        elif self.is_float(element):
            return "<float>"
        
        elif self.is_bool(element):
            return "<bool>"
        
        elif self.is_int_list(element):
            return "<int[]>"

        elif self.is_int_list(element):
            return "<float[]>"
        
        else:
            # Remove variable/function numberings if present
            element = re.sub(r"(<.*?>)[\d]+?", r"\1", element)

        return element


    def is_int(self, string):
        """
        Check if a string represents an integer.
        """
        try:
            int(string)
            return True
        except ValueError:
            return False


    def is_float(self, string):
        """
        Check if a string represents a float.
        """
        try:
            float(string)
            return True
        except ValueError:
            return False     


    def is_bool(self, string):
        """
        Check if a string represents a boolean.
        """
        if string in ["True", "False"]:
            return True

        return False


    def is_int_list(self, string):
        """
        Check if a string represents a list of integers.
        
        OBS: This just bases the list type on first element.
        Therefore, it is important that lists types are STATIC.
        """
        if string.startswith("[") and string.endswith("]"):
            if self.is_int(string.strip("[").strip("]").split(",")[0]):
                return True

        return False

    def is_float_list(self, string):
        """
        Check if a string represents a list of integers.
        
        OBS: This just bases the list type on first element.
        Therefore, it is important that lists types are STATIC.
        """
        if string.startswith("[") and string.endswith("]"):
            if self.is_float(string.strip("[").strip("]").split(",")[0]):
                return True

        return False


    def clone(self):
        """
        Return a new Instruction object with identical member values as self.
        """
        clone = Instruction(" ".join(self.template))
        clone.indent = self.indent
        clone.pre_compiled_elements = self.pre_compiled_elements.copy()

        return clone


    def __str__(self):
        """
        Return a complete string of the pre-compiled instruction.
        """
        indents = ""
        # Set the indentation
        for _ in range(self.indent):
            indents += "\t"

        return indents + " ".join(self.pre_compiled_elements)