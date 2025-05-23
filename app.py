from flask import Flask, request, render_template, jsonify
from flask_cors import CORS  # Import flask-cors
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# Alternatively, to restrict origins:
# CORS(app, resources={r"/api/*": {"origins": "https://meta.wikimedia.org"}})

# Regex to check if a line already has <translate> tags
# Updated regex to detect any presence of <translate> tags (including comments and spaces)
translate_tag_pattern = re.compile(r"<translate\b[^>]*>.*?</translate>", re.DOTALL)
# Regex to match attributes like rowspan, colspan, etc.
attribute_pattern = re.compile(r"\b\w+(?!==)=([^\s|]+)")
# Regex to detect table cell separators (| and ||)
table_cell_separator_pattern = re.compile(r"(\|\||\||\*)")
# Regex to detect headers in the format of == Header ==
header_pattern = re.compile(r"^(=+)(.*?)(=+)$")
# Regex to detect table header cell separators (! and !!)
header_cell_separator_pattern = re.compile(r"(!{1,2})")
# Regex to detect HTML entities (special characters)
special_char_pattern = re.compile(r"&\w+;")
# Regex for hiero, sub, sup, and math tags
# Matches text wrapped in <hiero>...</hiero> 
hiero_pattern = re.compile(r'(<hiero>.*?</hiero>)')
# Matches text wrapped in <sub>...</sub> tags or Unicode subscript characters (e.g., &#8320;).
sub_pattern = re.compile(r'(<sub>.*?</sub>|&#832[0-9];)')
# Matches text wrapped in <sup>...</sup> tags or Unicode superscript characters (e.g., &#8300;, &sup1;).
sup_pattern = re.compile(r'(<sup>.*?</sup>|&#830[0-9];|&sup[0-9];)')
# Matches text wrapped in <math>...</math> tags.
math_tag_pattern = re.compile(r'(<math>.*?</math>)')
# Matches {{math|...}} templates.
math_template_pattern = re.compile(r'(\{\{math\|.*?\}\})')
# Matches time strings in formats like "12:34", "3:45PM", or "11:00am".
time_pattern = re.compile(r'\b\d{1,2}:\d{2}(AM|PM|am|pm)?\b')
# Matches <gallery> and </gallery> tags.
gallery_pattern = re.compile(r'<gallery>|</gallery>')
# Matches occurrences of "File:".
file_pattern = re.compile(r'File:')
# Matches <br> tags.
br_pattern = re.compile(r'<br>')
# Matches magic words wrapped in double underscores (e.g., __NOTOC__).
magic_word = re.compile(r'__(.*?)__')
# Matches occurrences of the word "alt".
alt_pattern = re.compile(r'alt')
# Matches text inside double square brackets (e.g., [[example]]).
square_bracket_text_pattern = re.compile(r'\[\[(.*?)\]\]')
# Matches links with a pipe separator in double square brackets (e.g., [[link|display text]]).
square_bracket_with_pipeline_pattern = re.compile(r'\[\[([^\|\]]+)\|([^\]]+)\]\]')
# Matches occurrences of the '#'
existing_translation_pattern = re.compile(r'#')



def add_translate_tags(text):
    """
    Wraps the entire text in <translate> tags if it doesn't already have them,
    ensuring that special characters (e.g., &igrave;), time values (e.g., 9:30AM),
    and certain tags (e.g., hiero, sub, sup, math) are not wrapped in <translate> tags.
    Skips adding <translate> tags if they are already present, even with comments or special content.
    """
    if not text.strip():
        return text

    if re.search(r'<translate>.*<translate>', text):
        return text

    # If the text already has <translate> tags (including comments), do not add them
    if translate_tag_pattern.search(text):
        return text

    # If the text has any special characters, time values, or certain tags, don't wrap it in <translate> tags
    if (attribute_pattern.search(text) or special_char_pattern.match(text) or 
        hiero_pattern.search(text) or sub_pattern.search(text) or sup_pattern.search(text) or 
        time_pattern.match(text) or gallery_pattern.search(text) or file_pattern.search(text) or br_pattern.search(text) or magic_word.search(text)) :  # Skip time values
        return text
    # Wrap the entire block of text in <translate> tags
    return f'<translate>{text}</translate>'

def process_math(line):
    """
    Processes math-related tags ({{math}}, <math>, etc.) and ensures their content is not wrapped in <translate> tags.
    """
    # Generalized regex for math-related tags
    math_patterns = [
        re.compile(r'(\{\{math\|.*?\}\})', re.DOTALL),  # For {{math}} templates
        re.compile(r'(<math.*?>.*?</math>)', re.DOTALL)   # For <math> tags with attributes and content
    ]

    for pattern in math_patterns:
        match = pattern.search(line)
        if match:
            math_content = match.group(0)
            return line.replace(math_content, math_content)  # Return math-related content as is

    return line

def process_table_line(line):
    """
    Processes a single line of a table and adds <translate> tags where necessary,
    ensuring that only the actual content of table cells is wrapped, not the separators.
    """
    if not line:
        return line

    if line.startswith("|+"):
        # For table caption
        return f'{line[:2]}{add_translate_tags(line[2:].strip()) if len(line) > 2 else ""}'
    elif line.startswith("|-"):
        # Table row separator
        return line
    elif line.startswith("!"):
        # For table headers, split on ! and !! without breaking words
        headers = header_cell_separator_pattern.split(line)
        translated_headers = []
        for header in headers:
            if header in ['!', '!!']:  # Preserve the ! and !! without adding translate tags
                translated_headers.append(header)
            else:
                # Safely process header content
                processed_header = header.strip()
                if processed_header:
                    processed_header = process_external_link(processed_header)
                    processed_header = process_double_name_space(processed_header)
                    translated_headers.append(add_translate_tags(processed_header))
        return "".join(translated_headers)
    else:
        # For table rows, ensure content is wrapped but separators are untouched
        cells = table_cell_separator_pattern.split(line)
        translated_cells = []
        for cell in cells:
            if cell in ['|', '||', '*']:  # Leave separators as is
                translated_cells.append(cell)
            elif cell and cell.startswith("[["):
                # Process wiki links using process_double_name_space
                processed_cell = process_double_name_space(cell)
                translated_cells.append(processed_cell)
            elif cell and cell.startswith("http"):
                # Process external links
                processed_cell = process_external_link(cell)
                translated_cells.append(processed_cell)
            elif cell and cell.startswith("{{"):
                # Process double curly braces
                processed_cell = process_doublecurly(cell)
                translated_cells.append(processed_cell)
            elif cell:
                translated_cells.append(add_translate_tags(cell.strip()))
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
    match = header_pattern.match(line)
    if match:
        translated_header_text = add_translate_tags(match.group())
        return translated_header_text
    return line


def process_double_name_space(line):
    """
    Double Name space (e.g., [[link/eg]]) and adds <translate> tags around the eg text.
    Also handles simple internal links by adding Special:MyLanguage prefix.
    Properly handles text that appears after closing brackets by adding translate tags.
    Does not put translate tags around colons.
    """
    if 'Special:MyLanguage/' in line:  
        return line
    
    if line.lower().startswith("[[category:"):
        y = line.split(']]')[0]
        if not existing_translation_pattern.search(line):
            return y + '{{#translation:}}]]'
        else:
            return y + ']]'
    
    # Handle File case
    if len(line) > 6 and line[0:2] == "[[" and line[2:6] == "File":
        # File processing logic remains the same
        returnline = ""
        i = 0
        while i < len(line):
            if line[i:i+4] == 'alt=':
                returnline += "alt=<translate>"
                i += 4
                while i < len(line) and line[i] != '|' and line[i] != ']':
                    returnline += line[i]
                    i += 1
                returnline += "</translate>"
                if i < len(line):
                    returnline += line[i]
            else:
                if i < len(line) and line[i] == '|':
                    if i+1 < len(line) and line[i+1] == ' ':
                        if i+3 < len(line) and line[i+2:i+4] in ('left'):
                            returnline += line[i]
                        elif i+6 < len(line) and line[i+2:i+7] in ('right','center','thumb'):
                            returnline += line[i]
                        else:
                            returnline += "| <translate>"
                            i+=2
                            while i < len(line) and line[i] != '|' and line[i] != ']':
                                returnline += line[i]
                                i += 1
                            returnline += "</translate>"
                            if i < len(line):
                                returnline += line[i]
                    else:
                        if i+2 < len(line) and line[i+1:i+3] in ('left'):
                            returnline += line[i]
                        elif i+5 < len(line) and line[i+1:i+6] in ('right','center','thumb'):
                            returnline += line[i]
                        else:
                            returnline += "| <translate>"
                            i+=1
                            while i < len(line) and line[i] != '|' and line[i] != ']':
                                returnline += line[i]
                                i += 1
                            returnline += "</translate>"
                            if i < len(line):
                                returnline += line[i]
                else:
                     if i < len(line):
                         returnline += line[i]
            i += 1
        return returnline
    link_pattern = r'\[\[(.*?)\]\]'
    parts = re.split(link_pattern, line)
    
    result = ""
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part.strip():
                colon_parts = re.split(r'(:)', part)
                for j, cp in enumerate(colon_parts):
                    if cp == ':':  
                        result += cp
                    elif cp.strip():  
                        result += f"<translate>{cp}</translate>"
                    else:  
                        result += cp
            else:
                result += part
        else: 
            if '|' in part:
                link_target, link_text = part.split('|', 1)
                if not link_target.startswith(('Category:', 'File:', 'Special:')):
                    result += f'[[Special:MyLanguage/{link_target}|<translate>{link_text}</translate>]]'
                else:
                    result += f'[[{link_target}|<translate>{link_text}</translate>]]'
            else:
                if not part.startswith(('Category:', 'File:', 'Special:')):
                    result += f'[[Special:MyLanguage/{part}|<translate>{part}</translate>]]'
                else:
                    result += f'[[{part}]]'
    
    return result
def process_external_link(line):
    """
    Processes external links in the format [http://example.com Description] and ensures
    that only the description part is wrapped in <translate> tags, leaving the URL untouched.
    """
    match = re.match(r'(\[https?://[^\s]+)\s+([^\]]+)\]', line)

    if match:
        url_part = match.group(1)
        description_part = match.group(2)
        # Wrap only the description part in <translate> tags, leave the URL untouched
        return f'{url_part} <translate>{description_part}</translate>]'
    return line

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
                if "https://" in words[j]: 
                    words[j] = f"<translate>{words[j]}</translate>"
                elif "[[" in words[j]:
                    words[j] = process_double_name_space(words[j])
                else: 
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
            return f'{opening_tag}{translated_poem_content}{closing_tag}{convert_to_translatable_wikitext(line[end_idx+len(closing_tag):])}', False

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
def process_small_tag(line, in_poem_block=False):
    """
    Detects <poem> and </poem> tags and processes the text content inside the poem
    by wrapping it in <translate> tags. Handles cases where only one of the tags is present.
    
    :param line: The line of text to process.
    :param in_poem_block: A flag to indicate if we are already inside a <poem> block.
    :return: Processed line, and updated in_poem_block flag.
    """
    opening_poem_pattern = re.compile(r'(<small[^>]*>)', re.IGNORECASE)
    closing_poem_pattern = re.compile(r'(</small>)', re.IGNORECASE)
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
            return f'{opening_tag}{translated_poem_content}{closing_tag}{convert_to_translatable_wikitext(line[end_idx+len("</small>"):])}', False

        else:
            # If only the opening <poem> tag is present, we are in the middle of a poem block
            translated_poem_content = convert_to_translatable_wikitext(poem_content)
            return f'{opening_tag}{translated_poem_content}', True

    # Case 2: Detect a closing </poem> tag without an opening tag in the same line
    elif closing_poem_pattern.search(line) and not in_poem_block:

        closing_tag = closing_poem_pattern.search(line).group(1)  # Extract the closing </poem> tag
        poem_content = line[:line.find(closing_tag)].strip()  # Get content before the closing tag
        after_poem= line[line.find(closing_tag)+len(closing_tag):].strip()
        # Process the poem content by adding <translate> tags
        translated_poem_content = convert_to_translatable_wikitext(poem_content)
        # print(after_poem)
        translated_after_poem = convert_to_translatable_wikitext(after_poem)
        # Return the processed line with the closing </poem> tag
        return f'{translated_poem_content}{closing_tag}{after_poem}', False

    # Case 3: We are inside a <poem> block and no closing tag is found in this line
    elif in_poem_block:
        translated_poem_content = convert_to_translatable_wikitext(line.strip())
        return f'{translated_poem_content}', True

    # Case 4: No <poem> tag found, return the line as is
    return line, in_poem_block
# def process_big_tag(line, in_poem_block=False):
#     """
#     Detects <poem> and </poem> tags and processes the text content inside the poem
#     by wrapping it in <translate> tags. Handles cases where only one of the tags is present.
    
#     :param line: The line of text to process.
#     :param in_poem_block: A flag to indicate if we are already inside a <poem> block.
#     :return: Processed line, and updated in_poem_block flag.
#     """
#     opening_poem_pattern = re.compile(r'(<big[^>]*>)', re.IGNORECASE)
#     closing_poem_pattern = re.compile(r'(</big>)', re.IGNORECASE)
#     # Case 1: Detect an opening <poem> tag (without necessarily having a closing tag)
#     if opening_poem_pattern.search(line) and not in_poem_block:
#         opening_tag = opening_poem_pattern.search(line).group(1)  # Extract the opening <poem> tag
#         start_idx = line.find(opening_tag) + len(opening_tag)
#         print(line[:start_idx])
#         poem_content = line[start_idx:].strip()  # Get the content after the opening tag
#         # If there's a closing tag within the same line
#         if closing_poem_pattern.search(line):
#             closing_tag = closing_poem_pattern.search(line).group(1)  # Extract the closing </poem> tag
#             end_idx = line.find(closing_tag)
#             poem_content = line[start_idx:end_idx].strip()  # Get content between <poem> and </poem>

#             # Process the poem content by adding <translate> tags
#             translated_poem_content = convert_to_translatable_wikitext(poem_content)
#             # Return the fully processed line
#             return f'{convert_to_translatable_wikitext(line[:start_idx])}{opening_tag}{translated_poem_content}{closing_tag}{convert_to_translatable_wikitext(line[end_idx+len("</big>"):])}', False

#         else:
#             # If only the opening <poem> tag is present, we are in the middle of a poem block
#             translated_poem_content = convert_to_translatable_wikitext(poem_content)
#             return f'{opening_tag}{translated_poem_content}', True

#     # Case 2: Detect a closing </poem> tag without an opening tag in the same line
#     elif closing_poem_pattern.search(line) and not in_poem_block:

#         closing_tag = closing_poem_pattern.search(line).group(1)  # Extract the closing </poem> tag
#         poem_content = line[:line.find(closing_tag)].strip()  # Get content before the closing tag
#         print(line.find(closing_tag))
#         after_poem= line[line.find(closing_tag)+len(closing_tag):].strip()
#         # Process the poem content by adding <translate> tags
#         translated_poem_content = convert_to_translatable_wikitext(poem_content)
#         # print(after_poem)
#         translated_after_poem = convert_to_translatable_wikitext(after_poem)
#         # Return the processed line with the closing </poem> tag
#         return f'{translated_poem_content}{closing_tag}{after_poem}', False

#     # Case 3: We are inside a <poem> block and no closing tag is found in this line
#     elif in_poem_block:
#         translated_poem_content = convert_to_translatable_wikitext(line.strip())
#         return f'{translated_poem_content}', True

#     # Case 4: No <poem> tag found, return the line as is
#     return line, in_poem_block
def process_code_tag(line):
    """
    Processes <code> and </code> tags and ensures that the content inside the tags is not wrapped in <translate> tags.
    """
    if "<code" in line and "</code>" in line:
        before_code = line.split("<code>")[0].strip()
        code_content = line.split("<code>")[1].split("</code>")[0]
        after_code = line.split("</code>")[1].strip()

        translated_before = convert_to_translatable_wikitext(before_code) if before_code else ''
        translated_after = convert_to_translatable_wikitext(after_code) if after_code else ''

        return f'{translated_before}<code>{code_content}</code>{translated_after}'
    elif "<code>" in line:
        before_code = line.split("<code")[0].strip()
        code_content = line.split("<code")[1].strip()
        translated_before = convert_to_translatable_wikitext(before_code) if before_code else ''
        return f'{translated_before}<code>{code_content}'
    elif "</code>" in line:
        code_content = line.split("</code>")[0].strip()
        after_code = line.split("</code>")[1].strip()
        translated_after = convert_to_translatable_wikitext(after_code) if after_code else ''
        return f'{code_content}</code>{translated_after}'
    else:
        return line
def process_syntax_highlights(line):
    """
    Processes <syntaxhighlight> and </syntaxhighlight> tags and ensures that the content inside the tags is not wrapped in <translate> tags.
    """
    if "<syntaxhighlight" in line and "</syntaxhighlight>" in line:
        before_syntax = line.split("<syntaxhighlight>")[0].strip()
        syntax_content = line.split("<syntaxhighlight>")[1].split("</syntaxhighlight>")[0]
        after_syntax = line.split("</syntaxhighlight>")[1].strip()

        translated_before = convert_to_translatable_wikitext(before_syntax) if before_syntax else ''
        return f'{translated_before}<syntaxhighlight>{syntax_content}</syntaxhighlight>{after_syntax}'
    elif "<syntaxhighlight>" in line:
        before_syntax = line.split("<syntaxhighlight")[0].strip()
        syntax_content = line.split("<syntaxhighlight>")[1].strip()
        translated_before = convert_to_translatable_wikitext(before_syntax) if before_syntax else ''
        return f'{translated_before}<syntaxhighlight>{syntax_content}'
    elif "</syntaxhighlight>" in line:
        syntax_content = line.split("</syntaxhighlight>")[0].strip()
        after_syntax = line.split("</syntaxhighlight>")[1].strip()
        translated_after = convert_to_translatable_wikitext(after_syntax) if after_syntax else ''
        return f'{syntax_content}</syntaxhighlight>{translated_after}'
    else:
        return line
def convert_to_translatable_wikitext(wikitext):
    if wikitext == "":
        return ""
    """
    Converts standard wikitext to translatable wikitext by wrapping text with <translate> tags.
    Handles tables, lists, blockquotes, divs, and ensures tags inside blockquotes are not wrapped.
    """
    lines = re.split("\n",wikitext)
    converted_lines = []
    in_syntax_highlight = False
    in_table = False
    for line in lines:
        if line is not None:
            line = line.strip()
    

        if line:
            if "<syntaxhighlight" in line:
                # Start of a syntax highlight block
                in_syntax_highlight = True
                opening_tag_idx = line.index("<syntaxhighlight")
                # Process content before the opening tag
                converted_lines.append(convert_to_translatable_wikitext(line[:opening_tag_idx]))
                
                # Append the syntaxhighlight block as it is
                converted_lines.append(line[opening_tag_idx:])
            elif "</syntaxhighlight>" in line:
                # End of a syntax highlight block
                closing_tag_idx = line.index("</syntaxhighlight>")
                
                # Process content before the closing tag
                converted_lines.append(line[:closing_tag_idx])
                
                # Append the closing syntaxhighlight tag
                converted_lines.append(line[closing_tag_idx:])
                in_syntax_highlight = False  # Exiting syntax highlight mode
            elif in_syntax_highlight:
                # Inside a syntaxhighlight block, do not process the line
                converted_lines.append(line)
            elif line.startswith("'''"):
                converted_lines.append(process_lists(line))
            elif line.startswith("{|"):
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
            elif "<code" in line or "</code>" in line:
                converted_lines.append(process_code_tag(line))
            elif '<div' in line:
                converted_lines.append(process_div(line))  # Handle any <div> tag
            elif '</div>' in line:
                converted_lines.append(line)
            elif "<hiero>" in line or "</hiero>" in line:
                converted_lines.append(line)  # Do not add translate tags inside <hiero> tag
            elif sub_pattern.search(line) or sup_pattern.search(line):
                converted_lines.append(line)  # Do not add translate tags inside <sub>/<sup>
            elif "<math>" in line or "{{math}}" in line:
                converted_lines.append(process_math(line))  # Handle math tags
            elif "<small>" in line or "</small>" in line:
        # If the line contains <small> tags, we won't wrap them.
                converted_lines.append(process_small_tag(line)[0])
            else:
                converted_lines.append(add_translate_tags(line))
        else:
            converted_lines.append('')
        converted_lines = [str(line) if line is not None else "" for line in converted_lines]
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

@app.route('/api/convert', methods=['GET', 'POST'])
def api_convert():
    if request.method == 'GET':
        return """
        <h1>Translate Tagger API</h1>
        <p>Send a POST request with JSON data to use this API.</p>
        <p>Example:</p>
        <pre>
        curl -X POST https://translatetagger.toolforge.org/api/convert \\
        -H "Content-Type: application/json" \\
        -d '{"wikitext": "This is a test [[link|example]]"}'
        </pre>
        """
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'wikitext' not in data:
            return jsonify({'error': 'Missing "wikitext" in JSON payload'}), 400
        
        wikitext = data.get('wikitext', '')
        converted_text = convert_to_translatable_wikitext(wikitext)
        
        return jsonify({
            'original': wikitext,
            'converted': converted_text
        })

if __name__ == '__main__':
    app.run(debug=True)
