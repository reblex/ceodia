from src.code.elements.instruction import Instruction
from src.code.elements.scope import Scope

import numpy as np
import random
import re

MAX_INDENDT = 5

class CodeWriter():

    def __init__(self):
        self.scope = Scope()             # Currently scoped dynamic elements & other scope related stuff
        self.available_instructions = [] # All loaded instruction objects
        self.written_instructions = []   # Completed lines of code, represented as Instruction objects


    def load_instructions(self, path):
        """
        Load instructions from .tmpl-file and generate instruction objects.
        """
        
        # Add the "New Line Break" manually, which reduces indent when selected.
        instruction = Instruction("nlb")
        self.available_instructions.append(instruction)

        with open(path, "r") as file:
            for line in file.readlines():
                instruction = Instruction(line.strip("\n"))
                self.available_instructions.append(instruction)


    def write(self):
        """
        Write instructions untill the program is deemed finished.
        """
        
        # TODO: More intelligence behind the decision to end.
        # Currently 10% chance to end when endable.
        while not self.is_endable() or not random.randint(0, 100) < 10:

            # Find all currently writable instructions
            writable_instructions = self.find_writable_instructions()        

            # DEBUG            
            # for ins in writable_instructions:
            #     print(ins.template)

            # Select one
            selected_instruction = self.select_instruction(writable_instructions)
            
            # Set the indentation of the line
            selected_instruction.indent = self.scope.indent

            # Fill out dynamic elements and lock in the instruction to complete it.
            # Then update the current scope with variable/scope changes.
            completed_instruction = self.finalize_instruction(selected_instruction)

            # Finally add the completed instruction as a line of code.
            self.written_instructions.append(completed_instruction)


    def find_writable_instructions(self):
        """
        Go through all avaialbe(loaded) instructions and see which are able to
        be written in the current state.
        """

        # TODO: Order the checks so that the fastest ones are completed first for optimization.

        writable_instructions = []
        
        # Check the requirements for each instruction to be written to determine
        # which instructions are currently writable.
        # Continue to next instruction if any requirement is missing.
        for instruction in self.available_instructions:

            # Check 0:
            # Is the instruction trying to reduce indent below 0?
            # Or is the instruction trying to reduce indent JUST AFTER statement declaration?
            if instruction.template[0] == "nlb":
                if self.scope.indent == 0:
                    continue
                
                elif len(self.written_instructions) > 0:
                    if self.written_instructions[-1].is_statement():
                        continue

            # Check 1:
            # Would the instruction increase current indent past MAX_INDENT?
            if self.scope.indent == MAX_INDENDT and instruction.is_statement():
                continue

            # Check 2:
            # Are the required dynamic elements currently present in the code?
            requirements = instruction.get_required_elements()

            element_requirements_met = True
            for requirement in requirements:
                if not self.requirement_is_present(requirement):
                    element_requirements_met = False
                    break

            if not element_requirements_met:
                continue

            # Check 3:
            # Does the instruction require a function scope? In that case,
            # are we inside of a function?
            if instruction.must_be_in_function():
                if self.scope.in_function == None:
                    continue

            # Check 4:
            # Don't write functions inside of other functions.
            if instruction.template[0] == "def" and self.scope.in_function != None:
                continue


            # All checks have been passed. Instruction is currentyl writable.
            writable_instructions.append(instruction)

        return writable_instructions


    def select_instruction(self, writable_instructions):
        """
        Select one of the writable instructions.
        """
        # TODO: Actually use some intelligence here. (weighted list of writable instructions?)
        instruction = np.random.choice(writable_instructions)
        
        # Returned cloned as we don't want to edit the original instruction object.
        return instruction.clone()


    # TODO: Rename to "pre_compile" for clarity?
    def finalize_instruction(self, instruction):
        """
        Fill out all dynamic elements and lock in the instruction to complete it.
        Then update the current scope with variable/scope changes.
        """
        dynamic_element_tokens = instruction.get_dynamic_element_tokens()
        element_objects = []

        # DEBUG
        # print("finalizing", instruction.template)

        # Find suitable elements to replace the dynamic element tokens of the instruction.
        for token in dynamic_element_tokens:

            # Find all fitting elements based on the token.
            elements = self.get_dynamic_elements_of_type(token)

            # Select one.
            # TODO: Use some intelligence (weighted list of elements?)
            selected_element = np.random.choice(elements)
            element_objects.append(selected_element)

        self.scope = instruction.finalize(element_objects, self.scope)

        # DEBUG
        # print(">", instruction.pre_compiled_elements)

        return instruction

    def is_endable(self):
        """
        Determine if the code could compile if finalized at this stage.
        """
        endable = True

        if len(self.written_instructions) == 0:
            endable = False
        
        elif self.written_instructions[-1].is_statement():
            endable = False

        return endable
        


    def requirement_is_present(self, requirement):
        """
        Helper function for find_writable_instructions().
        Checks if an element is currently present at least once in the current scope.
        
        Similar to get_dynamic_elements_of_type(), but only checks for first occurrence for
        increased performance as this will be performed on every instruction.
        
        Requirement is an element token string, ex: "var<int>".
        """
        is_present = False
        
        if requirement.startswith("var"):
            type = re.findall(r"<(.*?)>", requirement)[0]
            if len(self.scope.vars[type]['available']) > 0:
                is_present = True

        elif requirement.startswith("avar"):
            type = re.findall(r"<(.*?)>", requirement)[0]
            if len(self.scope.avars[type]['available']) > 0:
                is_present = True

        elif requirement.startswith("func"):
            arg_types = re.findall(r"<(.*?)>", requirement)

            for func in self.scope.funcs['available']:
                if not len(arg_types) == len(func.param_types):
                    break

                # Make sure that all function parameters are matching.
                matching_args = True
                for i in range(len(arg_types)):
                    if not arg_types[i] == func.param_types[i]:
                        matching_args = False
                        break
                
                if matching_args:
                    # Don't allow function recursion.
                    if func == self.scope.in_function:
                        continue
                    else:
                        is_present = True
                        break

        else:
            raise Exception("Trying to check for dynamic requirement of static element.")

        return is_present


    def get_dynamic_elements_of_type(self, token):
        """
        Return a list of all element objects from self.scope that match the element token.
        
        Variables just need to be of the same type, whilst functions need to have
        the correct amount of parameters to match the amount of arguments, and those
        parameters need to be of the correct type, and appear in the correct order.

        Ex 1: token=var<int>
        Returns a list of all scoped variables of type int.
        
        Ex 2: token=func(avar<int>,avar<int>)
        Returns a list of all scoped functions where there are two integer parameters.
        """
        elements = []
        
        if token.startswith("var"):
            type = re.findall(r"<(.*?)>", token)[0]
            elements = self.scope.vars[type]['available']

        elif token.startswith("avar"):
            type = re.findall(r"<(.*?)>", token)[0]
            elements = self.scope.avars[type]['available']

        elif token.startswith("func"):
            arg_types = re.findall(r"<(.*?)>", token)

            for func in self.scope.funcs['available']:
                if len(arg_types) == len(func.param_types):
                    matching_args = True
                    for i in range(len(arg_types)):
                        if not arg_types[i] == func.param_types[i]:
                            matching_args = False
                            break
                    
                    if matching_args:
                        elements.append(func)

        # Static value dynamic elements.
        # TODO: Needs to be some logic/intelligence to this to 
        elif token == "int":
            return [str(random.randint(0, 5))]
        
        elif token == "bool":
            raise Exception("bool static value handling not implemented")

        return elements
