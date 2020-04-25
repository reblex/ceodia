from src.code.elements.instruction import Instruction

import itertools
import re

class TemplateHandler():

	def __init__(self):
		self.template_generators = [] # Template Generators represented as splitted lists
		self.templates = []

	def load_template_generators(self, path):
		"""Load Generators used to create all template permutations"""
		with open(path, "r") as file:
			lines = file.read().split("\n")
			for line in lines:
				if not line.startswith("#") and not line == "":
					self.template_generators.append(line.split(" "))

	def generate_templates(self):
		"""
		Generate template permutations from loaded template generators.
		"""
		for generator in self.template_generators:
			self.templates.extend(self.expand(generator))

	def save_templates(self, path):
		"""Save loaded/generated templates to file"""
		with open(path, "w+") as file:
			for template in self.templates:
				template_str = ' '.join(template) + "\n"
				file.write(template_str)

	def create_instructions(self, path):
		"""
		Load instructions from .tmpl-file and generate instruction objects.
		"""
		instructions = []

		# Add the "New Line Break" manually, which reduces indent when selected.
		instruction = Instruction("nlb")
		instructions.append(instruction)

		with open(path, "r") as file:
			for line in file.readlines():
				instruction = Instruction(line.strip("\n"))
				instructions.append(instruction)

		return instructions


	def load_existing_templates(self, path):
		"""Load previously generated templates"""
		pass


	def expand(self, template):
		"""
		Gather permutations from a specific Template Generator.
		"""

		# Make each element a list so we can figure out permutations.
		# Ex: [if, var<int>, {{<|>}}, <int>] would become [[if], [var<int>], [<, >], [<int>]]
		instruction_parts = []
		for element in template:
			if not "{{" in element:
				if element.startswith("var") or element.startswith("<"):
					instruction_parts.append(["{{" + element + "}}"])
				else:
					# Static element (like "return", "=", "def")
					instruction_parts.append([element])

			else:
				# Multiple options of tokens.
				# Find all permutations of the element.
				# func(|var<int>) becomes [func(), func(var<int>)]
				element_permutations = self.generate_element_permutations(element)
				instruction_parts.append(element_permutations)

		# Now find all permutations of the template
		permutations = []
		for template_permutation in itertools.product(*instruction_parts):
			permutations.append(list(template_permutation))

		return permutations


	def generate_element_permutations(self, element):
		"""
		Generate all permutations of an instruction element.
		"""
		permutation_parts = []
		for idx, dynamic in enumerate(re.findall(r"{{(.*)}}", element)):
			tokens = self.extract_tokens(dynamic)

			# Create Deep Permutations
			for i, token in enumerate(tokens):
				if "{{" in token:
					token_permutations = self.generate_element_permutations(token)
					del tokens[i]
					tokens.extend(token_permutations)

			element = element.replace("{{" + dynamic + "}}", "[[" + str(idx) + "]]", 1)

			permutation_parts.append(tokens)

		permutations = []
		for template_permutation in itertools.product(*permutation_parts):
			permutation = element
			for i in range(len(template_permutation)):

				repl = template_permutation[i]
				if not permutation.startswith("nfunc") and not permutation.startswith("func"):  
					if repl.startswith("var") or bool(re.match(r"<.*?>", repl)):                     
						if "," in repl:
							repls = repl.split(",")
							repl = ','.join(["{{" + elem + "}}" for elem in repls])
						else:
							repl = "{{" + repl + "}}"

				#DEBUG
				# print("replacing", "[[" + str(i) + "]]", "in", permutation, "with", repl)

				permutation = permutation.replace("[[" + str(i) + "]]", repl)

			if permutation.startswith("func"):
				permutation = "{{" + permutation + "}}"

			permutations.append(permutation)
		
		return permutations


	def extract_tokens(self, dynamic_part):
		"""
		Get all variations of dynamic parts in an element.
		"""
		tokens = []
		for token in self.optsplit(dynamic_part):
			tokens.append(token)

		return tokens


	def optsplit(self, string):
		"""
		Split options in string separated by "|".
		Do not split on "|" when inside of multivalue: {{}}
		"""
		parts = string.split("|")

		filtered_parts = []
		combo_parts = []
		for part in parts:
			if "{{" in part:
				combo_parts.append(part)
			
			elif "}}" in part:
				combo_parts.append(part)
				filtered_parts.append("|".join(combo_parts))
				combo_parts = []

			elif len(combo_parts) == 0:
				filtered_parts.append(part)

			else:
				combo_parts.append(part)

		return filtered_parts