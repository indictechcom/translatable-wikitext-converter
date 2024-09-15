from flask import Flask, request, render_template
import re

app = Flask(__name__)

def convert_to_translatable_wikitext(wikitext):
    # Split the input by lines
    lines = wikitext.split('\n')
    converted_lines = []

    # Regex to check if a line already has <translate> tags
    translate_tag_pattern = re.compile(r"<translate>.*</translate>")

    # Table flag to check if we are within a table
    in_table = False

    for line in lines:
        # Remove leading and trailing spaces
        line = line.strip()

        # Skip empty lines
        if line:
            # If the line already has <translate> tags, leave it unchanged
            if translate_tag_pattern.search(line):
                converted_lines.append(line)
            # Handle table start
            elif line.startswith("{|"):
                in_table = True
                converted_lines.append(line)  # Add table start line as is
            # Handle table end
            elif line.startswith("|}") and in_table:
                in_table = False
                converted_lines.append(line)  # Add table end line as is
            elif in_table:
                # Handle table captions
                if line.startswith("|+"):
                    converted_lines.append(f'<translate>{line[2:].strip()}</translate>')  # Table caption
                # Handle table row separators
                elif line.startswith("|-"):
                    converted_lines.append(line)  # Keep table row separator as is
                # Handle table headers
                elif line.startswith("!"):
                    headers = line.split("!")
                    translated_headers = [f"! <translate>{header.strip()}</translate>" for header in headers if header.strip()]
                    converted_lines.append(" ".join(translated_headers))  # Join headers back with '!'
                # Handle table cells
                elif line.startswith("|"):
                    cells = line.split("|")
                    translated_cells = [f"| <translate>{cell.strip()}</translate>" for cell in cells if cell.strip()]
                    converted_lines.append(" ".join(translated_cells))  # Join cells back with '|'
            # Handle section headings
            elif line.startswith('==') and line.endswith('=='):
                converted_lines.append(f'<translate>{line}</translate>')
            # Handle normal text
            else:
                converted_lines.append(f'<translate>{line}</translate>')
        else:
            # Preserve empty lines
            converted_lines.append('')

    # Join the converted lines back into a single string
    return '\n'.join(converted_lines)

@app.route('/')
def index():
    return render_template('home.html')

# Handle refresh by redirecting to the home page
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
