#!/usr/bin/env python3

from src.template_handler.template_handler import TemplateHandler
from src.code.code import Code
from src.compiler.compiler import Compiler



###
# Load Generators & Generate Templates.
# Then create instruction objects.
###
th = TemplateHandler()
th.load_template_generators("template_generators/main.txt")
th.generate_templates()
th.save_templates("templates/main.tmpl")

available_instructions = th.create_instructions("templates/main.tmpl")

# for ins in available_instructions:
# 	print(ins.template)

###
# Write Code & Pre-compile
###
code = Code(available_instructions)
# code.load_from_file("function-header.pytmpl")

# code.write_function()
code.write()

code.finalize()

# for instruction in code.written_instructions:
# 	print(str(instruction))

code.save_to_file("out.pytmpl")

###
# Compile to Pyhton3
###
compiler = Compiler()
compiled_lines = compiler.compile_and_write(code, "out.py")

# for line in compiled_lines:
#     print(line)
