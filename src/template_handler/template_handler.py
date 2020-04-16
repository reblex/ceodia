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
				# Just one option of token
				instruction_parts.append([element])

			else:
				# Multiple options of tokens.
				# Find all permutations of the element.
				# func(|avar<int>) becomes [func(), func(avar<int>)]
				
				dynamic_part = re.findall(r"{{(.*)}}", element)[0]
				static_part = re.sub(r"{{.*}}", "???", element)

				tokens = []
				for token in dynamic_part.split("|"):
					tokens.append(token)

				# Put in each avaialable dynamic part of the element into the static part.
				element_permutations = []
				for token in tokens:
					permutation = re.sub(r"\?\?\?", token, static_part)
					element_permutations.append(permutation)

				instruction_parts.append(element_permutations)

		# Now find all permutations of the template
		permutations = []
		for template_permutation in itertools.product(*instruction_parts):
			permutations.append(list(template_permutation))

		return permutations