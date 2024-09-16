from flask import Flask, request, render_template
import re

app = Flask(__name__)

# Regex to check if a line already has <translate> tags
translate_tag_pattern = re.compile(r"<translate>.*</translate>")
# Regex to match attributes like rowspan, colspan, etc.
attribute_pattern = re.compile(r"\b\w+=[^\s\|]+")
# Regex to detect table cell separators (| and ||)
table_cell_separator_pattern = re.compile(r"(\|\|?)")

def add_translate_tags(text):
    """
    Wraps the text in <translate> tags if it doesn't already have them
    and if it is not an attribute like rowspan=11.
    """
    # If it's an attribute (like rowspan=11), skip adding <translate> tags
    if attribute_pattern.search(text):
        return text
    if not translate_tag_pattern.search(text) and text.strip():
        return f'<translate>{text.strip()}</translate>'
    return text

def process_table_line(line):
    """
    Processes a single line of a table and adds <translate> tags where necessary,
    excluding attributes like rowspan or colspan and ensuring the | symbol remains intact.
    """
    if line.startswith("|+"):
        return f'<translate>{line[2:].strip()}</translate>'  # Table caption
    elif line.startswith("|-"):
        return line  # Keep table row separator as is
    elif line.startswith("!"):
        # For table headers, translate individual cells
        headers = table_cell_separator_pattern.split(line)
        translated_headers = [add_translate_tags(header) if not attribute_pattern.search(header) else header for header in headers]
        return "".join(translated_headers)  # Join back the headers
    elif line.startswith("|"):
        # Split by cell separators (| or ||), but keep separators intact and don't add tags to `|` alone
        cells = table_cell_separator_pattern.split(line)
        translated_cells = []
        for cell in cells:
            if cell.strip() == "|":  # Leave the | separator as is
                translated_cells.append(cell)
            else:
                # Add translate tags to non-attribute content
                translated_cells.append(add_translate_tags(cell) if not attribute_pattern.search(cell) else cell)
        return "".join(translated_cells)  # Join back the cells
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
            if line.startswith("{|"):
                in_table = True
                converted_lines.append(line)  # Table start
            elif line.startswith("|}") and in_table:
                in_table = False
                converted_lines.append(line)  # Table end
            elif in_table:
                converted_lines.append(process_table_line(line))
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
