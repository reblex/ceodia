#!/usr/bin/env python3

from src.template_handler.template_handler import TemplateHandler

th = TemplateHandler()
th.load_template_generators("template_generators/main.txt")
th.generate_templates()
th.save_templates("templates/main.tmpl")