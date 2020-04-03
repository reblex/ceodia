from src.code.elements.function import Function
from src.code.elements.variable import Variable
from src.code.elements.scope import Scope

import re

class Instruction():
    """Represents one line of Code"""

    def __init__(self, template):
        self.template = template.split(" ")  # List of elemnts in the instruction.
        self.indent = None                   # Indentation of the line (amount of tabs)
        self.dynamic_element_indexes = []    # Indexes of the template's dynamic elements.
        self.elements = self.template.copy() # Uncompiled elements. Mix of static strings & element objects.
        self.pre_compiled_elements = []      # All elements after pre-compilation.


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
        static values that just need to be filled in like "int" or "bool".
        """
        requirements = []
        for element in self.template:
            if element.startswith("var") or element.startswith("avar") or element.startswith("func"):
                requirements.append(element)

        return requirements


    def must_be_in_function(self):
        """
        Is the function required to be inside of a function?
        """
        for element in self.template:
            if element == "return" or element.startswith("avar"):
                return True

        return False


    def get_dynamic_element_tokens(self):
        """
        Return ALL element tokens that are required to be filled out in order to complete the instruction.
        This function also internally marks where those elements appear, which is used when
        completing the instruction.
        """
        dynamic_elements = []
        for i, element in enumerate(self.template):
            # Dynamic element Values
            if element in ["int", "bool"]:
                dynamic_elements.append(element)
                self.dynamic_element_indexes.append(i)
            
            # Variables and functions
            elif element.startswith("var") or element.startswith("avar") or element.startswith("func"):
                dynamic_elements.append(element)
                self.dynamic_element_indexes.append(i)

        return dynamic_elements


    def finalize(self, args, scope):
        """
        Fill out all dynamic elements of the instruction to complete it. Then update the scope.
        The dynamic elements are represented as a list(args) in order.
        Returns the updated scope.
        """

        # Make sure that all dynamic elements are being filled.
        if len(args) != len(self.dynamic_element_indexes):
            raise Exception("Incorrect number of dynamic elements when completing instruction.")

        # Make note if a function has called return.
        if self.elements[0] == "return":
            scope.in_function.has_returned = True

        # Replace dynamic elements with elements given by code_writer.
        for i, index in enumerate(self.dynamic_element_indexes):
            self.elements[index] = str(args[i])

        # Create variable/func objects, update scope etc.
        # And finally, pre-compile elements into tokens.
        for element in self.elements:

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
                for type in param_types:
                    # TODO: Move handling of creation of avars/vars/funcs to Scope class?
                    var_num = scope.avars[type]['num_created']
                    scope.avars[type]['num_created'] += 1
                    
                    var = Variable(type, scope.indent + 1, var_num, True)
                    param_arg_vars.append(var)
                    scope.avars[type]['available'].append(var)

                # Create the function object.
                func_num = scope.funcs['num_created']
                scope.funcs['num_created'] += 1
                
                func = Function(scope.indent, param_types, param_arg_vars, func_num, return_type)
                scope.funcs['available'].append(func)

                # Entering function body, mark what function it is so we know
                # when we are exiting it.
                scope.in_function = func

                self.pre_compiled_elements.append(str(func))

            # Creation of a "regular" variable.
            elif element.startswith("nvar"):
                type = re.findall(r"<(.*?)>", element)[0]
                var_num = scope.vars[type]['num_created']
                scope.vars[type]['num_created'] += 1
                
                var = Variable(type, scope.indent + 1, var_num)
                scope.vars[type]['available'].append(var)

                self.pre_compiled_elements.append(str(var))

            # Static elements are just appended, as they are already pre-compiled.
            else:
                self.pre_compiled_elements.append(element)


        # LASTLY!! Increase indent if this instruction is a statement.
        if self.is_statement():
            scope.indent += 1

        return scope


    def clone(self):
        """
        Returns a copy of self.
        """
        return Instruction(" ".join(self.template))


    def __str__(self):
        """
        Return a complete string of the pre-compiled instruction.
        """
        return " ".join(self.pre_compiled_elements)