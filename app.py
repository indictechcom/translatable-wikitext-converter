from flask import Flask, request, render_template, jsonify
from flask_cors import CORS  # Import flask-cors
import re
from enum import Enum
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

behaviour_switches = ['__NOTOC__', '__FORCETOC__', '__TOC__', '__NOEDITSECTION__', '__NEWSECTIONLINK__', '__NONEWSECTIONLINK__', '__NOGALLERY__', '__HIDDENCAT__', '__EXPECTUNUSEDCATEGORY__', '__NOCONTENTCONVERT__', '__NOCC__', '__NOTITLECONVERT__', '__NOTC__', '__START__', '__END__', '__INDEX__', '__NOINDEX__', '__STATICREDIRECT__', '__EXPECTUNUSEDTEMPLATE__', '__NOGLOBAL__', '__DISAMBIG__', '__EXPECTED_UNCONNECTED_PAGE__', '__ARCHIVEDTALK__', '__NOTALK__', '__EXPECTWITHOUTSCANS__']

# --- Helper Functions for Processing Different Wikitext Elements ---
# These functions are designed to handle specific wikitext structures.
# Some will recursively call the main `convert_to_translatable_wikitext`
# function to process their internal content, ensuring nested elements
# are also handled correctly.

def _wrap_in_translate(text):
    """
    Wraps the given text with <translate> tags.
    It ensures that empty or whitespace-only strings are not wrapped.
    The <translate> tags are added around the non-whitespace content,
    preserving leading and trailing whitespace.
    """
    if not text or not text.strip():
        return text

    # Find the first and last non-whitespace characters
    first_char_index = -1
    last_char_index = -1
    for i, char in enumerate(text):
        if char not in (' ', '\n', '\t', '\r', '\f', '\v'): # Check for common whitespace characters
            if first_char_index == -1:
                first_char_index = i
            last_char_index = i

    # If no non-whitespace characters are found (should be caught by text.strip() check, but for robustness)
    if first_char_index == -1:
        return text

    leading_whitespace = text[:first_char_index]
    content = text[first_char_index : last_char_index + 1]
    trailing_whitespace = text[last_char_index + 1 :]

    return f"{leading_whitespace}<translate>{content}</translate>{trailing_whitespace}"

def process_syntax_highlight(text):
    """
    Processes <syntaxhighlight> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<syntaxhighlight') and text.endswith('</syntaxhighlight>')), "Invalid syntax highlight tag"
    # Get inside the <syntaxhighlight> tag
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_table(text):
    """
    Processes table blocks in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('{|') and text.endswith('|}')), "Invalid table tag"
    return text

def process_blockquote(text):
    """
    Processes blockquote tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<blockquote>') and text.endswith('</blockquote>')), "Invalid blockquote tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_poem_tag(text):
    """
    Processes <poem> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<poem') and text.endswith('</poem>')), "Invalid poem tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_code_tag(text, tvar_code_id=0):
    """
    Processes <code> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<code') and text.endswith('</code>')), "Invalid code tag"
    # Get inside the <code> tag
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = f'<tvar name=code{tvar_code_id}>{content}</tvar>'
    return f"{prefix}{wrapped_content}{suffix}"

def process_div(text):
    """
    Processes <div> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<div') and text.endswith('</div>')), "Invalid div tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_hiero(text):
    """
    Processes <hiero> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<hiero>') and text.endswith('</hiero>')), "Invalid hiero tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_sub_sup(text):
    """
    Processes <sub> and <sup> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert((text.startswith('<sub>') and text.endswith('</sub>')) or
           (text.startswith('<sup>') and text.endswith('</sup>'))), "Invalid sub/sup tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_math(text):
    """
    Processes <math> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<math>') and text.endswith('</math>')), "Invalid math tag"
    return text

def process_small_tag(text):
    """
    Processes <small> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<small>') and text.endswith('</small>')), "Invalid small tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_nowiki(text):
    """
    Processes <nowiki> tags in the wikitext.
    It wraps the content in <translate> tags.
    """
    assert(text.startswith('<nowiki>') and text.endswith('</nowiki>')), "Invalid nowiki tag"
    start_tag_end = text.find('>') + 1
    end_tag_start = text.rfind('<')
    if start_tag_end >= end_tag_start:
        return text 
    prefix = text[:start_tag_end]
    content = text[start_tag_end:end_tag_start].strip()
    suffix = text[end_tag_start:]
    if not content:
        return text
    # Wrap the content in <translate> tags
    wrapped_content = _wrap_in_translate(content)
    return f"{prefix}{wrapped_content}{suffix}"

def process_item(text):
    """
    Processes list items in the wikitext.
    It wraps the content in <translate> tags.
    """
    offset = 0
    if text.startswith(';'):
        offset = 1
    elif text.startswith(':'):
        offset = 1
    elif text.startswith('#'):
        while text[offset] == '#':
            offset += 1
    elif text.startswith('*'):
        while text[offset] == '*':
            offset += 1
    # Add translate tags around the item content
    item_content = text[offset:].strip()
    if not item_content:
        return text
    return f"{text[:offset]} <translate>{item_content}</translate>\n"

def is_emoji_unicode(char):
    # This is a very simplified set of common emoji ranges.
    # A comprehensive list would be much longer and more complex.
    # See https://www.unicode.org/Public/emoji/ for full details.
    if 0x1F600 <= ord(char) <= 0x1F64F:  # Emoticons
        return True
    if 0x1F300 <= ord(char) <= 0x1F5FF:  # Miscellaneous Symbols and Pictographs
        return True
    if 0x1F680 <= ord(char) <= 0x1F6FF:  # Transport and Map Symbols
        return True
    if 0x2600 <= ord(char) <= 0x26FF:    # Miscellaneous Symbols
        return True
    if 0x2700 <= ord(char) <= 0x27BF:    # Dingbats
        return True
    # Add more ranges as needed for full coverage
    return False

class double_brackets_types(Enum):
    wikilink = 1
    category = 2
    inline_icon = 3
    not_inline_icon_file = 4
    special = 5
    invalid_file = 6

def _process_file(s, tvar_inline_icon_id=0): 
    # Define keywords that should NOT be translated when found as parameters
    NON_TRANSLATABLE_KEYWORDS = {
        'left', 'right', 'centre', 'center', 'thumb', 'frameless', 'border', 'none', 
        'upright', 'baseline', 'middle', 'sub', 'super', 'text-top', 'text-bottom', '{{dirstart}}', '{{dirend}}'
    }
    NON_TRANSLATABLE_KEYWORDS_PREFIXES = {
        'link=', 'upright='
    }
    NOT_INLINE_KEYWORDS = {
        'left', 'right', 'centre', 'center', 'thumb', 'frameless', 'border', 'none', '{{dirstart}}', '{{dirend}}'
    }
    file_aliases = ['File:', 'file:', 'Image:', 'image:']

    tokens = []
    
    inner_content = s[2:-2]  # Remove the leading [[ and trailing ]]
    tokens = inner_content.split('|')
    tokens = [token.strip() for token in tokens]  # Clean up whitespace around tokens
    
    # The first token shall start with a file alias
    # e.g., "File:Example.jpg" or "Image:Example.png"
    if not tokens or not tokens[0].startswith(tuple(file_aliases)):
        return line, double_brackets_types.invalid_file
    
    # The first token is a file link
    filename = tokens[0].split(':', 1)[1] if ':' in tokens[0] else tokens[0]
    tokens[0] = f'File:{filename}' 
    
    # Substitute 'left' with {{dirstart}}
    while 'left' in tokens:
        tokens[tokens.index('left')] = '{{dirstart}}'
    # Substitute 'right' with {{dirend}}
    while 'right' in tokens:
        tokens[tokens.index('right')] = '{{dirend}}'
    
    ############################
    # Managing inline icons
    #############################
    is_inline_icon = True
    for token in tokens:
        if token in NOT_INLINE_KEYWORDS:
            is_inline_icon = False
            break
    if is_inline_icon :
        # Check if it contains 'alt=' followed by an emoji
        for token in tokens:
            if token.startswith('alt='):
                alt_text = token[len('alt='):].strip()
                if not any(is_emoji_unicode(char) for char in alt_text):
                    is_inline_icon = False
                    break
    if is_inline_icon:
        # return something like: <tvar name="icon">[[File:smiley.png|alt=🙂]]</tvar>
        returnline = f'<tvar name=icon{tvar_inline_icon_id}>[[' + '|'.join(tokens) + ']]</tvar>'
        return returnline, double_brackets_types.inline_icon
    
    ############################
    # Managing general files
    #############################
    
    output_parts = []
    
    # The first token is the file name (e.g., "File:Example.jpg")
    # We substitute any occurrences of "Image:" with "File:"
    output_parts.append(tokens[0])

    pixel_regex = re.compile(r'\d+(?:x\d+)?px')  # Matches pixel values like "100px" or "100x50px)"
    for token in tokens[1:]:
        # Check for 'alt='
        if token.startswith('alt='):
            alt_text = token[len('alt='):].strip()
            output_parts.append('alt='+_wrap_in_translate(alt_text))
        # Check if the token is a known non-translatable keyword
        elif token in NON_TRANSLATABLE_KEYWORDS:
            output_parts.append(token)
        # If the token starts with a known non-translatable prefix, keep it as is
        elif any(token.startswith(prefix) for prefix in NON_TRANSLATABLE_KEYWORDS_PREFIXES):
            output_parts.append(token)
        # If the token is a pixel value, keep it as is
        elif pixel_regex.match(token):
            output_parts.append(token)
        # Otherwise, assume it's a caption or other translatable text
        else:
            output_parts.append(f"<translate>{token}</translate>")

    # Reconstruct the line with the transformed parts
    returnline = '[[' + '|'.join(output_parts) + ']]' 
    return returnline, double_brackets_types.not_inline_icon_file
    
def process_double_brackets(text, tvar_id=0):
    """
    Processes internal links in the wikitext.
    It wraps the content in <translate> tags.
    """
    if not (text.startswith("[[") and text.endswith("]]")) :
        print(f"Input >{text}< must be wrapped in double brackets [[ ]]")
        sys.exit(1)
    # Split the link into parts, handling both internal links and links with display text
    
    inner_wl = text[2:-2]  # Remove the leading [[ and trailing ]]
    parts = inner_wl.split('|')
    
    # part 0
    category_aliases = ['Category:', 'category:', 'Cat:', 'cat:']
    file_aliases = ['File:', 'file:', 'Image:', 'image:']
    
    parts[0] = parts[0].strip()  # Clean up the first part
    # Check if the first part is a category or file alias
    if parts[0].startswith(tuple(category_aliases)):
        # Handle category links
        cat_name = parts[0].split(':', 1)[1] if ':' in parts[0] else parts[0]
        return f'[[Category:{cat_name}{{{{#translation:}}}}]]', double_brackets_types.category
    elif parts[0].startswith(tuple(file_aliases)):
        # Handle file links
        return _process_file(text)
    elif parts[0].startswith('Special:'):
        # Handle special pages
        return f'[[{parts[0]}]]', double_brackets_types.special
    
    # Assuming it's a regular internal link
    if len(parts) == 1:
        return f'[[<tvar name={tvar_id}>Special:MyLanguage</tvar>/{parts[0].capitalize()}|{parts[0]}]]', double_brackets_types.wikilink
    if len(parts) == 2 :
        return f'[[<tvar name={tvar_id}>Special:MyLanguage</tvar>/{parts[0].capitalize()}|{parts[1]}]]', double_brackets_types.wikilink
    return text

def process_external_link(text, tvar_url_id=0):
    """
    Processes external links in the format [http://example.com Description] and ensures
    that only the description part is wrapped in <translate> tags, leaving the URL untouched.
    """
    match = re.match(r'\[(https?://[^\s]+)\s+([^\]]+)\]', text)

    if match:
        url_part = match.group(1)
        description_part = match.group(2)
        # Wrap only the description part in <translate> tags, leave the URL untouched
        return f'[<tvar name=url{tvar_url_id}>{url_part}</tvar> {description_part}]'
    return text

def process_template(text):
    """
    Processes the text to ensure that only the content outside of double curly braces {{ ... }} is wrapped in <translate> tags,
    while preserving the template content inside the braces without translating it.
    """
    assert(text.startswith('{{') and text.endswith('}}')), "Invalid template tag"
    # Split the template content from the rest of the text
    inner_content = text[2:-2]  # Remove the leading {{ and trailing }}
    
    # If the inner content is empty, return an empty string
    if not inner_content.strip():
        return text
    
    # Wrap the inner content in <translate> tags
    return f'{{{{<translate>{inner_content}</translate>}}}}'

def process_raw_url(text):
    """
    Processes raw URLs in the wikitext.
    It wraps the URL in <translate> tags.
    """
    # This function assumes the text is a raw URL, e.g., "http://example.com"
    # and wraps it in <translate> tags.
    if not text.strip():
        return text
    return f"<translate>{text.strip()}</translate>"


# --- Main Tokenisation Logic ---

def convert_to_translatable_wikitext(wikitext):
    """
    Converts standard wikitext to translatable wikitext by wrapping
    translatable text with <translate> tags, while preserving and
    correctly handling special wikitext elements.
    This function tokenizes the entire text, not line by line.
    """
    if not wikitext:
        return ""

    parts = []
    last = 0
    curr = 0
    text_length = len(wikitext)

    while curr < text_length :
        found = None
        # Syntax highlight block
        pattern = '<syntaxhighlight'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</syntaxhighlight>', curr) + len('</syntaxhighlight>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_syntax_highlight))
            curr = end_pos
            last = curr
            continue 
        # Table block
        pattern = '{|'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('|}', curr) + len('|}')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_table))
            curr = end_pattern
            last = curr
            continue
        # Blockquote
        pattern = '<blockquote>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</blockquote>', curr) + len('</blockquote>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_blockquote))
            curr = end_pattern
            last = curr
            continue
        # Poem tag
        pattern = '<poem'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</poem>', curr) + len('</poem>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_poem_tag))
            curr = end_pattern
            last = curr
            continue
        # Code tag
        pattern = '<code'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</code>', curr) + len('</code>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_code_tag))
            curr = end_pattern
            last = curr
            continue
        # Div tag
        pattern = '<div'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</div>', curr) + len('</div>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_div))
            curr = end_pattern
            last = curr
            continue
        # Hiero tag
        pattern = '<hiero>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</hiero>', curr) + len('</hiero>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_hiero))
            curr = end_pattern
            last = curr
            continue
        # Sub tag
        pattern = '<sub>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</sub>', curr) + len('</sub>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_sub_sup))
            curr = end_pattern
            last = curr
            continue
        # Sup tag
        pattern = '<sup>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</sup>', curr) + len('</sup>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_sub_sup))
            curr = end_pattern
            last = curr
            continue
        # Math tag
        pattern = '<math>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</math>', curr) + len('</math>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_math))
            curr = end_pattern
            last = curr
            continue
        # Small tag
        pattern = '<small>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</small>', curr) + len('</small>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_small_tag))
            curr = end_pattern
            last = curr
            continue
        # Nowiki tag
        pattern = '<nowiki>'
        if wikitext.startswith(pattern, curr):
            end_pattern = wikitext.find('</nowiki>', curr) + len('</nowiki>')
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pattern], process_nowiki))
            curr = end_pattern
            last = curr
            continue
        # br tag
        patterns = ['<br>', '<br/>', '<br />']
        for p in patterns:
            if wikitext.startswith(p, curr):
                end_pattern = curr + len(p)
                if last < curr:
                    parts.append((wikitext[last:curr], _wrap_in_translate))
                parts.append((wikitext[curr:end_pattern], lambda x: x))
                curr = end_pattern
                last = curr
                found = True
                break
        if found:
            continue
        # Lists
        patterns_newline = ['\n*', '\n#', '\n:', '\n;']
        if any(wikitext.startswith(p, curr) for p in patterns_newline) :
            curr += 1 # Discard the newline character
            parts.append((wikitext[last:curr], _wrap_in_translate))
            # Iterate through the list items
            patterns = ['*', '#', ':', ';']
            while any(wikitext.startswith(p, curr) for p in patterns) :
                end_pattern = wikitext.find('\n', curr)
                if end_pattern == -1:
                    end_pattern = text_length
                else :
                    end_pattern += 1 # Include the newline in the part
                parts.append((wikitext[curr:end_pattern], process_item))
                curr = end_pattern
                last = curr
            continue
        # Internal links
        pattern = '[['
        if wikitext.startswith(pattern, curr):
            # Count the number of opening double brackets '[[' and closing ']]' to find the end
            end_pos = curr + 2
            bracket_count = 1
            while end_pos < text_length and bracket_count > 0:
                if wikitext.startswith('[[', end_pos):
                    bracket_count += 1
                    end_pos += 2
                elif wikitext.startswith(']]', end_pos):
                    bracket_count -= 1
                    end_pos += 2
                else:   
                    end_pos += 1
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            if end_pos > curr + 2:  # Ensure we have a valid link
                parts.append((wikitext[curr:end_pos], process_double_brackets))
            curr = end_pos
            last = curr
            continue
        # External links
        pattern = '[http'
        if wikitext.startswith(pattern, curr):
            # Find the end of the external link
            end_pos = wikitext.find(']', curr)
            if end_pos == -1:
                end_pos = text_length
            else :
                end_pos += 1 # Include the closing ']' in the part
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pos + 1], process_external_link))
            curr = end_pos
            last = curr
            continue
        # Templates
        pattern = '{{'
        if wikitext.startswith(pattern, curr):
            # Find the end of the template
            end_pos = wikitext.find('}}', curr) + 2
            if end_pos == 1:
                end_pos = text_length
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pos], process_template))
            curr = end_pos
            last = curr
            continue
        # Raw URLs
        pattern = 'http'
        if wikitext.startswith(pattern, curr):
            # Find the end of the URL (space or end of string)
            end_pos = wikitext.find(' ', curr)
            if end_pos == -1:
                end_pos = text_length
            if last < curr:
                parts.append((wikitext[last:curr], _wrap_in_translate))
            parts.append((wikitext[curr:end_pos], process_raw_url))
            curr = end_pos
            last = curr
            continue
        # Behaviour switches
        for switch in behaviour_switches:
            if wikitext.startswith(switch, curr):
                end_pos = curr + len(switch)
                if last < curr:
                    parts.append((wikitext[last:curr], _wrap_in_translate))
                parts.append((wikitext[curr:end_pos], lambda x: x))
                curr = end_pos
                last = curr
                
        
        curr += 1  # Move to the next character if no pattern matched
        
    # Add any remaining text after the last processed part
    if last < text_length:
        parts.append((wikitext[last:], _wrap_in_translate))
    
    
    print ('*' * 20)
    for i, (part, handler) in enumerate(parts):
        print(f"--- Start element {i} with handler {handler.__name__} ---")
        print(part) 
        print(f"---\n") 
        
    print ('*' * 20)
    
    
    # Process links
    tvar_id = 0
    tvar_url_id = 0
    tvar_code_id = 0
    tvar_inline_icon_id = 0
    for i, (part, handler) in enumerate(parts):
        # Handlers for links require a tvar_id
        if handler == process_double_brackets:
            new_part, double_brackets_type = handler(part, tvar_id)
            if double_brackets_type in [double_brackets_types.wikilink, double_brackets_types.special, double_brackets_types.inline_icon]:
                new_handler = _wrap_in_translate  # Change handler to _wrap_in_translate
            else :
                new_handler = lambda x: x  # No further processing for categories and files
            parts[i] = (new_part, new_handler)
            tvar_id += 1
        elif handler == process_external_link:
            new_part = handler(part, tvar_url_id)
            new_handler = _wrap_in_translate  # Change handler to _wrap_in_translate
            parts[i] = (new_part, new_handler)
            tvar_url_id += 1
        elif handler == process_code_tag:
            new_part = handler(part, tvar_code_id)
            new_handler = _wrap_in_translate  # Change handler to _wrap_in_translate
            parts[i] = (new_part, new_handler)
            tvar_code_id += 1
        elif handler == process_double_brackets :
            new_part, double_brackets_type = handler(part, tvar_inline_icon_id)
            if double_brackets_type == double_brackets_types.inline_icon:
                new_handler = _wrap_in_translate  # Change handler to _wrap_in_translate
                tvar_inline_icon_id += 1
            else:
                new_handler = lambda x: x
            
    # Scan again the parts: merge consecutive parts handled by _wrap_in_translate
    _parts = []
    if parts:
        current_part, current_handler = parts[0]
        for part, handler in parts[1:]:
            if handler == _wrap_in_translate and current_handler == _wrap_in_translate:
                # Merge the parts
                current_part += part
            else:
                _parts.append((current_part, current_handler))
                current_part, current_handler = part, handler
        # Add the last accumulated part
        _parts.append((current_part, current_handler))
        
    # Process the parts with their respective handlers
    processed_parts = [handler(part) for part, handler in _parts]            
    
    # Debug output
    """
    print("Processed parts:")
    for i, (ppart, (part, handler)) in enumerate(zip(processed_parts, _parts)):
        print(f"--- Start element {i} with handler {handler.__name__} ---")
        print(part)
        print(f"---\n") 
        print(ppart)  
        print(f"---\n") 
    """
    
    # Join the processed parts into a single string
    return ''.join(processed_parts)

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
