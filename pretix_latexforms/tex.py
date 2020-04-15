import jinja2
import os
from jinja2 import Template
import subprocess
import tempfile
latex_jinja_env = jinja2.Environment(
    block_start_string = r'\BLOCK{',
    block_end_string = r'}',
    variable_start_string = r'\VAR{',
    variable_end_string = r'}',
    comment_start_string = r'\#{',
    comment_end_string = r'}',
    line_statement_prefix = r'%%',
    line_comment_prefix = r'%#',
    trim_blocks = True,
    autoescape = False,
)
class TexError(Exception):

    def __init__(self, log, source):
        self.message = log
        self.source = source

    def __str__(self):
        return self.message

def render_tex(tex, latex_interpreter="xelatex"):
    with tempfile.TemporaryDirectory() as tempdir:
        filename = os.path.join(tempdir, 'texput.tex')
        with open(filename, 'x', encoding='utf-8') as f:
            f.write(tex)
        latex_command = f'cd "{tempdir}" && {latex_interpreter} -shell-escape -interaction=batchmode {os.path.basename(filename)}'
        process = subprocess.run(latex_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            if process.returncode == 1:
                with open(os.path.join(tempdir, 'texput.log'), encoding='utf8') as f:
                    log = f.read()
                raise TexError(log=log, source=tex)
            with open(os.path.join(tempdir, 'texput.pdf'), 'rb') as pdf_file:
                pdf = pdf_file.read()
        except:
            if process.stderr:
                raise Exception(process.stderr.decode('utf-8'))
            raise
    return pdf
