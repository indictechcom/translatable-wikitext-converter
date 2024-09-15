from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def convert_to_translatable_wikitext(wikitext):
    lines = wikitext.split('\n')
    converted_lines = []
    
    for line in lines:
        if line.strip():
            if line.startswith('==') and line.endswith('=='):
                converted_lines.append(f'<translate>{line}</translate>')
            else:
                converted_lines.append(f'<translate>{line.strip()}</translate>')
        else:
            converted_lines.append('')
    
    return '\n'.join(converted_lines)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/convert', methods=['POST'])
def convert():
    wikitext = request.form.get('wikitext', '')
    converted_text = convert_to_translatable_wikitext(wikitext)
    return render_template('home.html', original=wikitext, converted=converted_text)

if __name__ == '__main__':
    app.run(debug=True)
