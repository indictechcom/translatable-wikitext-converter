from flask import Flask, request, render_template
import re

app = Flask(__name__)

def convert_to_translatable_wikitext(wikitext):
    # Split the input by lines
    lines = wikitext.split('\n')
    converted_lines = []
    
    # Regex to check if a line already has <translate> tags
    translate_tag_pattern = re.compile(r"<translate>.*</translate>")

    for line in lines:
        # Skip empty lines
        if line.strip():
            # If the line already has <translate> tags, leave it unchanged
            if translate_tag_pattern.search(line):
                converted_lines.append(line)
            # If it's a section heading, add <translate> tags around it
            elif line.startswith('==') and line.endswith('=='):
                converted_lines.append(f'<translate>{line.strip()}</translate>')
            # Otherwise, add <translate> tags around normal text
            else:
                converted_lines.append(f'<translate>{line.strip()}</translate>')
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
