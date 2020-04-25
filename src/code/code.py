from src.code.elements.instruction import Instruction
from src.code.elements.scope import Scope
from src.code.elements.function import Function

import numpy as np
import random
import re

MAX_INDENDT = 5

class Code():

    def __init__(self, available_instructions):
        self.scope = Scope()                                 # Currently scoped dynamic elements & other scope related stuff
        self.available_instructions = available_instructions # All loaded instruction objects
        self.written_instructions = []                       # Completed lines of code, represented as Instruction objects


    def write_function(self):
        """
        Write a single function.
        """
        self.write('single-function')


    def write(self, special=None):
        """
        Write instructions untill the program is deemed finished.
        """

        while True:

            # Find all currently writable instructions
            writable_instructions = self.find_writable_instructions()        

            # DEBUG            
            # for ins in writable_instructions:
            #     print(ins.template)

            # Select one
            selected_instruction = self.select_instruction(writable_instructions)
            
            # If the writer determines code to be finished.
            if selected_instruction == None:
                break

            print("Selecting Instruction(" + str(len(self.written_instructions)+1) + "):", selected_instruction.template)

            # Complete the instruction and add it to written instructions
            self.write_instruction(selected_instruction)
            print("Pre-compiled Instruction:", selected_instruction.pre_compiled_elements)
            print("\n")

            # Handle specific stopping points.
            if special == "single-function" and len(self.written_instructions) > 0:
                if self.written_instructions[-1].template[0] == "return":
                    break

            # DEBUG
            # print("Instruction Count:", len(self.written_instructions), "Num Funcs", self.scope.funcs['num_created'], "Current Indent:", self.scope.indent)


    def write_instruction(self, instruction):
        """
        Complete and pre-compile a selected instruction and
        add it to the list of written instructions.
        """
        
        # Set the indentation of the line
        instruction.indent = self.scope.indent

        # Fill out dynamic elements and lock in the instruction to complete it.
        # Then update the current scope with variable/scope changes.
        completed_instruction = self.precompile_instruction(instruction)

        # Finally add the completed instruction as a line of code.
        self.written_instructions.append(completed_instruction)


    def finalize(self):
        """
        When the code is complete, remove unnecessary stuff.
        """
        self.available_instructions = None
        self.scope = None


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

            # Check -1:
            # If the function has return in the first indentation level of the body, you have to call nlb.
            # Otherwise the code will be unreachable.
            # And...
            # Do not return in void-function
            # AND...
            # Do not return on any other indent rather than the most inner body indent. 
            if self.scope.in_function != None:    
                if self.scope.indent == self.scope.in_function.indent + 1:
                    if self.written_instructions[-1].template[0] == "return" and instruction.template[0] != "nlb":
                        continue

                if instruction.template[0] == "return":
                    if self.scope.in_function.return_type == "void":
                        continue

                    if self.scope.indent != self.scope.in_function.indent + 1:
                        continue

            # Check 0:
            # Is the instruction trying to reduce indent below 0?
            # Or is the instruction trying to reduce indent JUST AFTER statement declaration?
            # OR... Is the instruction trying to exit non-void function before return?
            if instruction.template[0] == "nlb":
                if self.scope.indent == 0:
                    continue
                
                if len(self.written_instructions) > 0:
                    if self.written_instructions[-1].is_statement():
                        continue

                if self.scope.in_function != None:
                    if self.scope.indent == self.scope.in_function.indent + 1:
                        if not self.scope.in_function.has_returned:
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
            # Don't write functions on indent above 0.
            if instruction.template[0] == "def" and self.scope.indent != 0:
                continue


            # All checks have been passed. Instruction is currently writable.
            writable_instructions.append(instruction.clone())

        return writable_instructions


    def select_instruction(self, writable_instructions):
        """
        Select one of the writable instructions.
        """

        # If there are no more instruction left to write, return None to
        # finish the code. This happens if a function has return and the
        # indent has been reduced to 0 when only writing a single function.
        if len(writable_instructions) == 0:
            return None

        # If there is just one avaialble instruction just return it.
        # This can happen when the only thing left avaialable is "nlb".
        if len(writable_instructions) == 1:
            return writable_instructions[0]

        # Determine relevance of each instruction.
        # Relevance is scored from 1-100, with a baseline of 50.
        # 
        # OBS: Relevance is currently not capped at 100!      
        #
        # OBS: relevance != percentual chance to get picked.
        # Score will be converted into probabilities based on each
        # instructions individual score, so a higher score means
        # a larger chance to get selected, but never 0% or 100%.
        instruction_relevance = [50 for _ in writable_instructions]
        
        # If the code is currently endable, add the end instruction (None).
        if self.is_endable():
            instruction_relevance.append(50)
            writable_instructions.append(None)

        for i, instruction in enumerate(writable_instructions):
            relevance = 50
            
            if instruction == None:
                # TODO: there should probably be a lot more going into this decision.
                relevance = 100
                relevance += len(self.written_instructions) * 5

            elif instruction.template[0] == "nlb":
                # The higher the value of current indentation, the larger the
                # chance to reduce indentation.
                relevance += 10 * self.scope.indent
                relevance += len(self.written_instructions) * 5

            elif instruction.is_statement():
                # Reduce chance to increase indentation the higher the current indentation,
                # when at or above indent 2.
                if self.scope.indent > 1:
                    relevance -= 15 * self.scope.indent
                    relevance -= len(self.written_instructions) * 5

            elif instruction.template[0] == "return":
                # The more lines in a function, the more likely to return.
                # The option to return is only available when on the first level
                # of indentation of the function, but all lines in the function count.
                relevance += 5 * self.scope.nr_instructions_in_func    


            # Keep relevance within 1-100.
            # instruction_relevance[i] = max(1, min(100, relevance))
            instruction_relevance[i] = max(1, relevance)


        # Calculate normalizer, using: (1 / (sum of relevance)).
        normalizer = 1 / float(sum(instruction_relevance))

        # Multiply each value by the normalizer to determine probabilities.
        probabilities = [relevance * normalizer for relevance in instruction_relevance]

        # Select species based on probability
        selected_instruction = np.random.choice(writable_instructions, 1, p=probabilities)[0]

        # TODO: Already cloning all writable.. for some reason. Don't remember why.
        # # Return a clone, as we don't want to edit the original instruction object.
        # if selected_instruction != None:
        #     selected_instruction = selected_instruction.clone()

        return selected_instruction


    # TODO: Rename to "pre_compile" for clarity?
    def precompile_instruction(self, instruction):
        """
        Fill out all dynamic elements and lock in the instruction to complete it.
        Then update the current scope with variable/scope changes.
        """ 
        dynamic_element_tokens = instruction.get_dynamic_element_tokens()
        element_args = []
        print("Dynamic Elements:", dynamic_element_tokens)


        # Find suitable elements to replace the dynamic element tokens of the instruction.
        for token in dynamic_element_tokens:

            # Find all fitting elements based on the token.
            elements = self.get_dynamic_elements_of_type(token)
            # Select one.
            # TODO: Use some intelligence (weighted list of elements?) Similar to select_instruction()
            selected_element = np.random.choice(elements)
            
            # A call to a self-created function also requires the needed
            # arguments for that function.
            if isinstance(selected_element, Function):
                arguments = []
                for arg_type in selected_element.param_types:
                    dynamic_type = "var<" + arg_type + ">"
                    vars = self.get_dynamic_elements_of_type(dynamic_type)

                    # TODO: Intelligence over selection here aswell maybeeeee.
                    argument = np.random.choice(vars)
                    arguments.append(argument)
                
                selected_element = [selected_element]
                selected_element.extend(arguments)

            element_args.append(selected_element)

        print("Element Replacements:", element_args)

        self.scope = instruction.precompile(element_args, self.scope)


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

        elif self.scope.in_function != None:
            if not self.scope.in_function.has_returned:
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
            var_type = re.findall(r"<(.*?)>", requirement)[0]
            if len(self.scope.vars[var_type]['available']) > 0:
                is_present = True

        elif requirement.startswith("func"):
            return_type = re.findall(r"func<(.*?)>", requirement)[0]
            arg_types = re.findall(r"var<(.*?)>", requirement)

            # Make sure the arguments are available
            for arg_type in arg_types:
                if len(self.scope.vars[arg_type]['available']) == 0:
                    break

            for func in self.scope.funcs['available']:
                if not len(arg_types) == len(func.param_types):
                    break

                # Correct return type (void/int/bool etc.)
                if func.return_type != return_type:
                    continue

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
        
        Ex 2: token=func(var<int>,var<int>)
        Returns a list of all scoped functions where there are two integer parameters.
        """
        elements = []
        
        if token.startswith("var"):
            var_type = re.findall(r"<(.*?)>", token)[0]
            elements = self.scope.vars[var_type]['available']

        elif token.startswith("func"):
            return_type = re.findall(r"func<(.*?)>", token)[0]
            
            # TODO: This way only variables can be passed to func.
            # Could use re.findall(r"v\((.*)\)", token).split(",") to get all arguements of any type.
            arg_types = re.findall(r"var<(.*?)>", token)

            for func in self.scope.funcs['available']:
                # Check for correct return type (void/int/bool etc.)
                if func.return_type != return_type:
                    continue

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
        elif token == "<int>":
            return [str(random.randint(0, 5))]
        
        elif token == "<float>":
            return [str(round(random.uniform(0, 5), 2))]
        
        elif token == "<bool>":
            return [np.random.choice(["True", "False"])]

        elif token == "<int[]>":
            return ["[]"]

        elif token == ["<float[]>"]:
            return ["[]"]

        return elements


    def save_to_file(self, path):
        """
        Write pre-compiled code to file.
        """
        with open(path, "w") as file:
            for instruction in self.written_instructions:
                file.write(str(instruction) + "\n")


    def load_from_file(self, path):
        """
        Load pre-compiled code back into instruction objects.
        """
        lines = []
        with open(path, "r") as file:
            lines = file.read().splitlines()

        for line in lines:
            instruction = Instruction()
            self.scope = instruction.load(line, self.scope)
            self.written_instructions.append(instruction)


    def clone(self):
        """
        Return a new Code object with identical member values as self.
        OBS: Cannot be used after calling finalize().
        """
        if self.available_instructions == None:
            raise Exception("Trying to clone finalized Code.")
        
        clone = Code(self.available_instructions)
        
        instruction_clones = []
        for instruction in self.written_instructions:
            instruction_clones.append(instruction.clone())

        clone.written_instructions = instruction_clones

        clone.scope = self.scope.clone()