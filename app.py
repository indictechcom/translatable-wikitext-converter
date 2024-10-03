from flask import Flask, request, render_template
import re

app = Flask(__name__)

# Regex to check if a line already has <translate> tags
translate_tag_pattern = re.compile(r"<translate>.*</translate>")
# Regex to match attributes like rowspan, colspan, etc.
attribute_pattern = re.compile(r"\b\w+=[^\s\|]+")
# Regex to detect table cell separators (| and ||)
table_cell_separator_pattern = re.compile(r"(\|\||\||\*)")
# Regex to detect headers in the format of == Header ==
header_pattern = re.compile(r"^(=+)(.*?)(=+)$")
# Regex to detect table header cell separators (! and !!)
header_cell_separator_pattern = re.compile(r"(!{1,2})")

def add_translate_tags(text):
    """
    Wraps the text in <translate> tags if it doesn't already have them
    and if it is not an attribute like rowspan=11.
    """
    if not text.strip():
        return text
    return f'<translate>{text.strip()}</translate>'

def process_table_line(line):
    """
    Processes a single line of a table and adds <translate> tags where necessary,
    ensuring that only the actual content of table cells is wrapped, not the separators.
    """
    if line.startswith("|+"):
        if line[2:].strip() == "":
            return line
        # For table caption
        return f'{line[0:2]}<translate>{line[2:].strip()}</translate>'
    elif line.startswith("|-"):
        # Table row separator
        return line
    elif line.startswith("!"):
        # For table headers, split on ! and !!
        headers = header_cell_separator_pattern.split(line)
        translated_headers = []
        for header in headers:
            if header in ['!', '!!']:  # Preserve the ! and !! without adding translate tags
                translated_headers.append(header)
            else:
                translated_headers.append(add_translate_tags(header))
        return "".join(translated_headers)
    else:
        # For table rows, ensure content is wrapped but separators are untouched
        cells = table_cell_separator_pattern.split(line)
        translated_cells = []
        for cell in cells:
            if cell in ['|', '||', '*']:  # Leave separators as is
                translated_cells.append(cell)
            elif cell.startswith("{{"):
                translated_cells.append(cell)
            elif cell.endswith("}}"):
                translated_cells.append(add_translate_tags(cell[:-2])+"}}")
            else:
                translated_cells.append(add_translate_tags(cell))
        return "".join(translated_cells)

def process_div(line):
    """
    Processes any <div> tag and adds <translate> tags around the text content inside the div,
    while keeping the div structure and attributes intact.
    """
    # Regex pattern to detect <div> tags
    div_pattern = re.compile(r'(<div[^>]*>)(.*?)(</div>)', re.DOTALL)
    match = div_pattern.search(line)

    if match:
        opening_div_tag = match.group(1)  # <div ... >
        div_content = match.group(2)  # Text or content inside the div
        closing_div_tag = match.group(3)  # </div>

        # Wrap only the text content inside the div with <translate> tags
        translated_content = add_translate_tags(div_content.strip())

        return f'{opening_div_tag}{translated_content}{closing_div_tag}'
    return line

def process_header(line):
    """
    Processes headers (e.g., == Header ==) and adds <translate> tags around the header text.
    """
    match = header_pattern.match(line)
    if match:
        # Extract the equal signs and the header content
        opening_equals = match.group(1)
        header_text = match.group(2).strip()
        closing_equals = match.group(3)
        # Wrap only the header text with <translate> tags, keep the equal signs intact
        return f'{opening_equals} <translate>{header_text}</translate> {closing_equals}'
    return line

def process_double_name_space(line):
    """
    Double Name space (e.g., [[link/eg]]) and adds <translate> tags around the eg text.
    """
    pipestart = False
    returnline = ""

    # For File case
    if line[2:6] == "File":
        i = 0
        while i < len(line):
            if line[i:i+4] == 'alt=':
                returnline += "alt=<translate>"
                i += 4
                while line[i] != '|' and line[i] != ']':
                    returnline += line[i]
                    i += 1
                returnline += "</translate>"
                returnline += line[i]
            else:
                returnline += line[i]
            i += 1
        return returnline

    # For normal pipe name spaces
    line1 = line[2:-2]
    words = line1.split("|")

    if len(words) > 1:
        returnline += "[["
        returnline += words[0] + "|"
        words = words[1:]

        for word in words:
            if word.strip() != "":
                returnline += "<translate>"
                returnline += word
                returnline += "</translate>"
            else:
                returnline += "|"
        returnline += "]]"
        return returnline

    # For cases without pipe (just links)
    else:
        for i in range(len(line)):
            if line[i] == '|' and pipestart is False:
                pipestart = True
                returnline += "|<translate>"

            elif pipestart is True and (line[i] == '|' or line[i] == ']'):
                pipestart = False
                returnline += "</translate>"
                returnline += line[i]
                if line[i] == '|':
                    returnline += "<translate>"
                    pipestart = True
            else:
                returnline += line[i]
        return returnline

def process_external_link(line):
    """
    External link (e.g., [http://example.com]) and adds <translate> tags around the header text.
    """
    words = line.split()
    str=words[0]
    words=words[1:]
    words[-1] = words[-1][:-1]
    return f"{str} <translate>{' '.join(words)}</translate>]"

def process_lists(line):
    """
    Processes lists (e.g., *, #, :) by adding <translate> tags around list item content.
    """
    for i in range(len(line)):
        if line[i] in ['*', '#', ':', ';']:
            continue
        else:
            words = line[i:].split("<br>")
            for j in range(len(words)):
                worder = words[j].split(":")
                for k in range(len(worder)):
                    if worder[k] == '':
                        continue
                    else:
                        worder[k] = f"<translate>{worder[k]}</translate>"
                words[j] = ":".join(worder)
            newstring = "<br>".join(words)
            return f"{line[:i]}{newstring}"

def process_doublecurly(line):
    """
    Processes the text to ensure that only the content outside of double curly braces {{ ... }} is wrapped in <translate> tags,
    while preserving the template content inside the braces without translating it.
    """
    if "{{" in line and "}}" in line:
        start = line.index("{{")
        end = line.index("}}") + 2  # Include the closing "}}"
        inside_curly = line[start:end]
        outside_curly = line[end:].strip()
        if outside_curly:
            return f"{line[:start]}<translate>{outside_curly}</translate>"
        return inside_curly
    else:
        return f"<translate>{line.strip()}</translate>"

def process_blockquote(line):
    """
    Handles blockquote tags by ensuring content inside blockquote is not wrapped in <translate> tags.
    """
    if "<blockquote>" in line and "</blockquote>" in line:
        before_blockquote = line.split("<blockquote>")[0].strip()
        blockquote_content = line.split("<blockquote>")[1].split("</blockquote>")[0]
        after_blockquote = line.split("</blockquote>")[1].strip()

        translated_before = add_translate_tags(before_blockquote) if before_blockquote else ''
        translated_after = add_translate_tags(after_blockquote) if after_blockquote else ''

        return f'{translated_before}<blockquote>{blockquote_content}</blockquote>{translated_after}'
    elif "<blockquote>" in line:
        before_blockquote = line.split("<blockquote>")[0].strip()
        blockquote_content = line.split("<blockquote>")[1].strip()
        translated_before = add_translate_tags(before_blockquote) if before_blockquote else ''
        return f'{translated_before}<blockquote>{blockquote_content}'
    elif "</blockquote>" in line:
        blockquote_content = line.split("</blockquote>")[0].strip()
        after_blockquote = line.split("</blockquote>")[1].strip()
        translated_after = add_translate_tags(after_blockquote) if after_blockquote else ''
        return f'{blockquote_content}</blockquote>{translated_after}'
    else:
        return line
def process_poem_tag(line, in_poem_block=False):
    """
    Detects <poem> and </poem> tags and processes the text content inside the poem
    by wrapping it in <translate> tags. Handles cases where only one of the tags is present.
    
    :param line: The line of text to process.
    :param in_poem_block: A flag to indicate if we are already inside a <poem> block.
    :return: Processed line, and updated in_poem_block flag.
    """
    opening_poem_pattern = re.compile(r'(<poem[^>]*>)', re.IGNORECASE)
    closing_poem_pattern = re.compile(r'(</poem>)', re.IGNORECASE)
    # Case 1: Detect an opening <poem> tag (without necessarily having a closing tag)
    if opening_poem_pattern.search(line) and not in_poem_block:
        opening_tag = opening_poem_pattern.search(line).group(1)  # Extract the opening <poem> tag
        start_idx = line.find(opening_tag) + len(opening_tag)
        poem_content = line[start_idx:].strip()  # Get the content after the opening tag

        # If there's a closing tag within the same line
        if closing_poem_pattern.search(line):
            closing_tag = closing_poem_pattern.search(line).group(1)  # Extract the closing </poem> tag
            end_idx = line.find(closing_tag)
            poem_content = line[start_idx:end_idx].strip()  # Get content between <poem> and </poem>

            # Process the poem content by adding <translate> tags
            translated_poem_content = convert_to_translatable_wikitext(poem_content)

            # Return the fully processed line
            return f'{opening_tag}{translated_poem_content}{closing_tag}', False

        else:
            # If only the opening <poem> tag is present, we are in the middle of a poem block
            translated_poem_content = convert_to_translatable_wikitext(poem_content)
            return f'{opening_tag}{translated_poem_content}', True

    # Case 2: Detect a closing </poem> tag without an opening tag in the same line
    elif closing_poem_pattern.search(line) and not in_poem_block:

        closing_tag = closing_poem_pattern.search(line).group(1)  # Extract the closing </poem> tag
        poem_content = line[:line.find(closing_tag)].strip()  # Get content before the closing tag
        print(line.find(closing_tag))
        after_poem= line[line.find(closing_tag)+len(closing_tag):].strip()
        # Process the poem content by adding <translate> tags
        translated_poem_content = convert_to_translatable_wikitext(poem_content)
        # print(after_poem)
        translated_after_poem = convert_to_translatable_wikitext(after_poem)
        # Return the processed line with the closing </poem> tag
        return f'{translated_poem_content}{closing_tag}{after_poem}', False

    # Case 3: We are inside a <poem> block and no closing tag is found in this line
    elif in_poem_block:
        print(line)
        translated_poem_content = convert_to_translatable_wikitext(line.strip())
        return f'{translated_poem_content}', True

    # Case 4: No <poem> tag found, return the line as is
    return line, in_poem_block

def convert_to_translatable_wikitext(wikitext):
    if wikitext == "":
        return ""
    """
    Converts standard wikitext to translatable wikitext by wrapping text with <translate> tags.
    Handles tables, lists, blockquotes, divs, and ensures tags inside blockquotes are not wrapped.
    """
    lines = wikitext.split('\n')
    converted_lines = []

    in_table = False
    for line in lines:
        line = line.strip()

        if line:
            if line.startswith("{|"):
                in_table = True
                converted_lines.append(line)
            elif line.startswith("|}") and in_table:
                in_table = False
                converted_lines.append(line)
            elif in_table:
                converted_lines.append(process_table_line(line))
            elif header_pattern.match(line):
                converted_lines.append(process_header(line))
            elif line.startswith("http"):
                converted_lines.append(line)
            elif line.startswith("[["):
                converted_lines.append(process_double_name_space(line))
            elif line.startswith("["):
                converted_lines.append(process_external_link(line))
            elif line.startswith("<nowiki>"):
                converted_lines.append(line)
            elif line.startswith("*") or line.startswith("#") or line.startswith(":") or line.startswith(";"):
                converted_lines.append(process_lists(line))
            elif line.startswith("{{"):
                converted_lines.append(process_doublecurly(line))
            elif "<blockquote>" in line or "</blockquote>" in line:
                converted_lines.append(process_blockquote(line))
            elif "<poem" in line or "</poem>" in line:
                converted_lines.append(process_poem_tag(line)[0])
            elif '<div' in line:
                converted_lines.append(process_div(line))  # Handle any <div> tag
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
