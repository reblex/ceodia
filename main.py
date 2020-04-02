#!/usr/bin/env python3

from src.template_handler.template_handler import TemplateHandler
from src.code.code_writer import CodeWriter

th = TemplateHandler()
th.load_template_generators("template_generators/main.txt")
th.generate_templates()
th.save_templates("templates/main.tmpl")

cw = CodeWriter()
cw.load_instructions("templates/main.tmpl")

# for ins in cw.available_instructions:
# 	print(ins.template)

cw.write()
for instruction in cw.written_instructions:
	print(str(instruction))
