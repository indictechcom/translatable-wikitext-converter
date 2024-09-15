from flask import Flask, request, render_template
import re

app = Flask(__name__)

# Regex to check if a line already has <translate> tags
translate_tag_pattern = re.compile(r"<translate>.*</translate>")

def add_translate_tags(text):
    """
    Wraps the text in <translate> tags if it doesn't already have them.
    """
    if not translate_tag_pattern.search(text):
        return f'<translate>{text.strip()}</translate>'
    return text

def process_table_line(line, in_table):
    """
    Processes a single line of a table and adds <translate> tags where necessary.
    """
    if line.startswith("|+"):
        return f'<translate>{line[2:].strip()}</translate>'  # Table caption
    elif line.startswith("|-"):
        return line  # Keep table row separator as is
    elif line.startswith("!"):
        headers = line.split("!")
        translated_headers = [f"! <translate>{header.strip()}</translate>" for header in headers if header.strip()]
        return " ".join(translated_headers)  # Join headers back with '!'
    elif line.startswith("|"):
        cells = line.split("|")
        translated_cells = [f"| <translate>{cell.strip()}</translate>" for cell in cells if cell.strip()]
        return " ".join(translated_cells)  # Join cells back with '|'
    return line

def convert_to_translatable_wikitext(wikitext):
    """
    Converts standard wikitext to translatable wikitext by wrapping text with <translate> tags.
    Handles tables and preserves their structure.
    """
    lines = wikitext.split('\n')
    converted_lines = []

    in_table = False

    for line in lines:
        line = line.strip()

        if line:
            if translate_tag_pattern.search(line):
                converted_lines.append(line)
            elif line.startswith("{|"):
                in_table = True
                converted_lines.append(line)
            elif line.startswith("|}") and in_table:
                in_table = False
                converted_lines.append(line)
            elif in_table:
                converted_lines.append(process_table_line(line, in_table))
            elif line.startswith('==') and line.endswith('=='):
                converted_lines.append(add_translate_tags(line))
            else:
                converted_lines.append(add_translate_tags(line))
        else:
            converted_lines.append('')

    return '\n'.join(converted_lines)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/convert', methods=['GET'])
def redirect_to_home():
    return render_template('home.html')

@app.route('/convert', methods=['POST'])
def convert():
    wikitext = request.form.get('wikitext', '')
    converted_text = convert_to_translatable_wikitext(wikitext)
    return render_template('home.html', original=wikitext, converted=converted_text)

if __name__ == '__main__':
    app.run(debug=True)
