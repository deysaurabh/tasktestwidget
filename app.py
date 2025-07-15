from flask import Flask, render_template, request, session
from datetime import datetime
import re
import json


app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

def detect_dropdowns(code_snippet):
    """Detect dropdown placeholders in code snippet"""
    # Look for the specific JSON dropdown pattern and other common patterns
    dropdown_patterns = [
        # Amazon Connect widget specific patterns - more permissive
        r'Dropdown_\d+',
        r'"_id"\s*:\s*"Dropdown_',
        r'"Type"\s*:\s*"Dropdown"',
        r'"CCS_ACH_Back_End_PRC"',  # Specific option in your code snippet
        r'"CCS_ACH_Front_End_PRC"',  # Specific option in your code snippet
        # More general patterns for the Amazon Connect widget
        r'"Options"\s*:\s*\[',
        r'"Label"\s*:\s*"Work Queue"',
        # Alternative pattern for the same structure
        r'"Dropdown"[^}]*"Props"',
        # Traditional HTML patterns
        r'<select[^>]*>.*?</select>',
        r'\{\{dropdown\}\}',
        r'\[dropdown\]',
        r'<dropdown>',
        r'dropdown\s*=\s*\[\]'
    ]
    
    print("Analyzing code snippet for dropdowns...")
    
    # Debug: Print the first 100 characters of the code snippet
    print(f"Code snippet preview: {code_snippet[:100]}...")
    
    for pattern in dropdown_patterns:
        match = re.search(pattern, code_snippet, re.IGNORECASE | re.DOTALL)
        if match:
            print(f"Dropdown detected with pattern: {pattern}")
            print(f"Matched text: {match.group(0)}")
            return True
    
    print("No dropdown patterns matched.")
    return False

def replace_dropdown_placeholder(code_snippet, options):
    """Replace dropdown placeholder with actual HTML select element or updated JSON"""
    print(f"Replacing dropdown options with: {options}")
    
    # Create a simple JSON array of options in the format needed
    json_options = []
    for option in options:
        json_options.append({"Label": option, "Value": option})
    
    new_options_json = json.dumps(json_options)
    print(f"New options JSON: {new_options_json}")
    
    # For the Amazon Connect widget, we need to find the "Options" array and replace it
    try:
        # First, try to parse the viewConfig JSON
        start_idx = code_snippet.find('amazon_connect(\'viewConfig\', \'')
        if start_idx != -1:
            # Extract the JSON string
            json_start = start_idx + len('amazon_connect(\'viewConfig\', \'')
            json_end = code_snippet.find('\');', json_start)
            
            if json_end != -1:
                # Get the JSON string and unescape it
                json_str = code_snippet[json_start:json_end].replace('\\\"', '"').replace('\\\\', '\\')
                
                # Parse the JSON
                try:
                    # We need to handle the escaped JSON string
                    # First, try to parse it directly
                    view_config = json.loads(json_str)
                    
                    # Find the dropdown in the content
                    if 'content' in view_config and 'template' in view_config['content']:
                        template = view_config['content']['template']
                        if 'Body' in template:
                            for body_item in template['Body']:
                                if 'Content' in body_item:
                                    for content_item in body_item['Content']:
                                        if '_id' in content_item and content_item['_id'].startswith('Dropdown_'):
                                            # Found the dropdown, replace its options
                                            if 'Props' in content_item and 'Options' in content_item['Props']:
                                                content_item['Props']['Options'] = json_options
                                                print("Found and replaced dropdown options in JSON")
                    
                    # Convert back to JSON string
                    updated_json_str = json.dumps(view_config)
                    
                    # Replace in the original code snippet
                    updated_code = code_snippet[:json_start] + updated_json_str + code_snippet[json_end:]
                    print("Successfully updated dropdown options in viewConfig")
                    return updated_code
                except json.JSONDecodeError:
                    print("Error parsing JSON, falling back to regex replacement")
    except Exception as e:
        print(f"Error in JSON parsing approach: {e}")
    
    # If JSON parsing failed, fall back to regex replacement
    print("Using regex replacement as fallback")
    
    # Simple pattern to find the Options array
    options_pattern = r'("Options"\s*:\s*)\[[^\]]*\]'
    
    def replace_options(match):
        return match.group(1) + new_options_json
    
    # Try the replacement
    updated_code = re.sub(options_pattern, replace_options, code_snippet, flags=re.IGNORECASE | re.DOTALL)
    
    # Check if replacement was successful
    if updated_code != code_snippet:
        print("Successfully replaced dropdown options with regex")
        return updated_code
    else:
        print("No replacement made, returning original code")
        # If no replacement was made, create a simple demonstration of the options
        options_demo = f"/* Selected options: {', '.join(options)} */\n{code_snippet}"
        return options_demo

def create_select_html(options):
    """Create HTML select element with given options"""
    options_html = create_options_html(options)
    return f'<select>{options_html}</select>'

def create_options_html(options):
    """Create HTML option elements"""
    return ''.join([f'<option value="{opt}">{opt}</option>' for opt in options])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'analyze_code':
            code_snippet = request.form.get('code', '')
            session['code_snippet'] = code_snippet
            
            if detect_dropdowns(code_snippet):
                print("Dropdown detected")  # Output to console as requested
                session['has_dropdowns'] = True
                session['dropdown_options'] = []
                return render_template('index.html', 
                                     code_snippet=code_snippet,
                                     has_dropdowns=True,
                                     show_options_form=True,
                                     dropdown_options=[],
                                     dropdown_detected_message="Dropdown detected",
                                     current_date=datetime.now().strftime('%Y-%m-%d'))
            else:
                # No dropdowns detected, render directly
                session['has_dropdowns'] = False
                return render_template('index.html',
                                     code_snippet=code_snippet,
                                     rendered_code=code_snippet,
                                     current_date=datetime.now().strftime('%Y-%m-%d'))
        
        elif action == 'add_option':
            new_option = request.form.get('new_option', '').strip()
            if new_option:
                options = session.get('dropdown_options', [])
                if new_option not in options:
                    options.append(new_option)
                    session['dropdown_options'] = options
            
            return render_template('index.html',
                                 code_snippet=session.get('code_snippet', ''),
                                 has_dropdowns=True,
                                 show_options_form=True,
                                 dropdown_options=session.get('dropdown_options', []),
                                 current_date=datetime.now().strftime('%Y-%m-%d'))
        
        elif action == 'remove_option':
            option_to_remove = request.form.get('option_to_remove', '')
            options = session.get('dropdown_options', [])
            if option_to_remove in options:
                options.remove(option_to_remove)
                session['dropdown_options'] = options
            
            return render_template('index.html',
                                 code_snippet=session.get('code_snippet', ''),
                                 has_dropdowns=True,
                                 show_options_form=True,
                                 dropdown_options=options,
                                 current_date=datetime.now().strftime('%Y-%m-%d'))
        
        elif action == 'submit_options':
            code_snippet = session.get('code_snippet', '')
            options = session.get('dropdown_options', [])
            
            if options:
                # Update the code snippet with the new options
                updated_code = replace_dropdown_placeholder(code_snippet, options)
                # Use the updated code as both the code snippet and rendered code
                rendered_code = updated_code
                # Update the session with the new code snippet
                session['code_snippet'] = updated_code
                
                print("Updated code snippet with new options")
                print(f"Options: {options}")
            else:
                rendered_code = code_snippet
                updated_code = code_snippet
            
            return render_template('index.html',
                                 code_snippet=updated_code,  # Show updated code in input area
                                 rendered_code=rendered_code,
                                 current_date=datetime.now().strftime('%Y-%m-%d'))
        
        elif action == 'skip_options':
            code_snippet = session.get('code_snippet', '')
            return render_template('index.html',
                                 code_snippet=code_snippet,
                                 rendered_code=code_snippet,
                                 current_date=datetime.now().strftime('%Y-%m-%d'))
    
    # GET request - show initial form
    return render_template('index.html', current_date=datetime.now().strftime('%Y-%m-%d'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

