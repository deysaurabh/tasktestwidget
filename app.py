from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_cors import CORS
from datetime import datetime
import re
import json
import sqlite3
import os
import uuid


app = Flask(__name__)
# Enable CORS for all domains on all routes
CORS(app, resources={r'*':{'origins':'*'}})
app.secret_key = 'your-secret-key-here'  # Change this in production

# Database setup
DATABASE_PATH = 'snippets.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    # Use the app config if available, otherwise use the global variable
    db_path = app.config.get('DATABASE_PATH', DATABASE_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create snippets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS snippets (
        id TEXT PRIMARY KEY,
        original_code TEXT NOT NULL,
        rendered_code TEXT,
        has_dropdowns BOOLEAN NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create dropdown_options table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dropdown_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snippet_id TEXT NOT NULL,
        option_text TEXT NOT NULL,
        FOREIGN KEY (snippet_id) REFERENCES snippets (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

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

def save_snippet(code_snippet, has_dropdowns=False, rendered_code=None):
    """Save a code snippet to the database and return its ID"""
    snippet_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO snippets (id, original_code, rendered_code, has_dropdowns) VALUES (?, ?, ?, ?)',
        (snippet_id, code_snippet, rendered_code, has_dropdowns)
    )
    
    conn.commit()
    conn.close()
    
    return snippet_id

def get_snippet(snippet_id):
    """Get a snippet from the database by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM snippets WHERE id = ?', (snippet_id,))
    snippet = cursor.fetchone()
    
    if snippet:
        # Get dropdown options if any
        cursor.execute('SELECT option_text FROM dropdown_options WHERE snippet_id = ?', (snippet_id,))
        options = [row['option_text'] for row in cursor.fetchall()]
    else:
        options = []
    
    conn.close()
    
    return snippet, options

def save_dropdown_option(snippet_id, option_text):
    """Save a dropdown option for a snippet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO dropdown_options (snippet_id, option_text) VALUES (?, ?)',
        (snippet_id, option_text)
    )
    
    conn.commit()
    conn.close()

def remove_dropdown_option(snippet_id, option_text):
    """Remove a dropdown option for a snippet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'DELETE FROM dropdown_options WHERE snippet_id = ? AND option_text = ?',
        (snippet_id, option_text)
    )
    
    conn.commit()
    conn.close()

def get_dropdown_options(snippet_id):
    """Get all dropdown options for a snippet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT option_text FROM dropdown_options WHERE snippet_id = ?', (snippet_id,))
    options = [row['option_text'] for row in cursor.fetchall()]
    
    conn.close()
    
    return options

def update_rendered_code(snippet_id, rendered_code):
    """Update the rendered code for a snippet"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE snippets SET rendered_code = ? WHERE id = ?',
        (rendered_code, snippet_id)
    )
    
    conn.commit()
    conn.close()

@app.route('/reset', methods=['POST'])
def reset_app():
    """Reset the app to initial state by clearing session"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for AWS App Runner"""
    try:
        # Test database connection
        conn = get_db_connection()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'message': 'Application is running correctly',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Show the initial form"""
    # For JSON requests, return API info
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'api_version': '1.0',
            'description': 'Code Snippet Dropdown Manager API',
            'endpoints': {
                'analyze': '/analyze (POST)',
                'view_snippet': '/snippet/<snippet_id> (GET)',
                'configure_options': '/snippet/<snippet_id>/options (GET, POST)',
                'api_docs': '/api/docs (GET)',
                'health': '/health (GET)'
            }
        })
    
    # Get the last code snippet from session for the re-analyze button
    last_code_snippet = session.get('last_code_snippet', '')
    
    return render_template('index.html', 
                         current_date=datetime.now().strftime('%Y-%m-%d'),
                         previous_code_snippet=last_code_snippet)

@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation endpoint"""
    docs = {
        'api_version': '1.0',
        'description': 'Code Snippet Dropdown Manager API',
        'endpoints': [
            {
                'path': '/analyze',
                'method': 'POST',
                'description': 'Analyze a code snippet for dropdowns',
                'request_body': {
                    'code': 'The code snippet to analyze'
                },
                'response': {
                    'snippet_id': 'The ID of the saved snippet',
                    'has_dropdowns': 'Boolean indicating if dropdowns were detected',
                    'next_url': 'URL to configure options or view the snippet'
                }
            },
            {
                'path': '/snippet/<snippet_id>',
                'method': 'GET',
                'description': 'View a snippet',
                'response': {
                    'snippet_id': 'The ID of the snippet',
                    'original_code': 'The original code snippet',
                    'rendered_code': 'The rendered code with dropdown options applied',
                    'has_dropdowns': 'Boolean indicating if dropdowns were detected',
                    'options': 'Array of dropdown options',
                    'created_at': 'Timestamp when the snippet was created'
                }
            },
            {
                'path': '/snippet/<snippet_id>/options',
                'method': 'GET',
                'description': 'Get dropdown options for a snippet',
                'response': {
                    'snippet_id': 'The ID of the snippet',
                    'options': 'Array of dropdown options',
                    'original_code': 'The original code snippet'
                }
            },
            {
                'path': '/snippet/<snippet_id>/options',
                'method': 'POST',
                'description': 'Configure dropdown options for a snippet',
                'request_body': {
                    'action': 'The action to perform (add_option, remove_option, submit_options, skip_options)',
                    'new_option': 'The option to add (for add_option action)',
                    'option_to_remove': 'The option to remove (for remove_option action)'
                },
                'response': {
                    'snippet_id': 'The ID of the snippet',
                    'options': 'Array of dropdown options',
                    'message': 'A message describing the result of the action',
                    'rendered_code': 'The rendered code with dropdown options applied (for submit_options action)',
                    'view_url': 'URL to view the snippet (for submit_options and skip_options actions)'
                }
            }
        ],
        'example_usage': {
            'analyze': {
                'curl': 'curl -X POST -H "Content-Type: application/json" -d \'{"code": "<your code snippet>"}\' http://localhost:5000/analyze',
                'javascript': 'fetch("http://localhost:5000/analyze", {\n  method: "POST",\n  headers: {\n    "Content-Type": "application/json"\n  },\n  body: JSON.stringify({\n    code: "<your code snippet>"\n  })\n}).then(response => response.json()).then(data => console.log(data));'
            }
        }
    }
    
    return jsonify(docs)

@app.route('/analyze', methods=['POST'])
def analyze_code():
    """Analyze a code snippet for dropdowns"""
    # Check if the request is JSON or form data
    if request.is_json:
        data = request.get_json()
        code_snippet = data.get('code', '')
    else:
        code_snippet = request.form.get('code', '')
    
    # Store the current code snippet in session for re-analysis
    session['last_code_snippet'] = code_snippet
    
    has_dropdowns = detect_dropdowns(code_snippet)
    
    # Save the snippet to the database
    # If no dropdowns detected, set rendered_code to the original code
    rendered_code = code_snippet if not has_dropdowns else None
    snippet_id = save_snippet(code_snippet, has_dropdowns, rendered_code)
    
    # If it's a JSON request, return JSON response
    if request.is_json:
        return jsonify({
            'snippet_id': snippet_id,
            'has_dropdowns': has_dropdowns,
            'next_url': url_for('configure_options', snippet_id=snippet_id) if has_dropdowns else url_for('view_snippet', snippet_id=snippet_id)
        })
    
    # Otherwise, redirect as usual for form submissions
    if has_dropdowns:
        print("Dropdown detected")  # Output to console as requested
        return redirect(url_for('configure_options', snippet_id=snippet_id))
    else:
        # No dropdowns detected, render directly
        return redirect(url_for('view_snippet', snippet_id=snippet_id))

@app.route('/snippet/<snippet_id>', methods=['GET'])
def view_snippet(snippet_id):
    """View a snippet"""
    snippet, options = get_snippet(snippet_id)
    
    if not snippet:
        return jsonify({"error": "Snippet not found"}), 404 if request.is_json else ("Snippet not found", 404)
    
    # For JSON requests, return the snippet data
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'snippet_id': snippet_id,
            'original_code': snippet['original_code'],
            'rendered_code': snippet['rendered_code'] or snippet['original_code'],
            'has_dropdowns': snippet['has_dropdowns'],
            'options': options,
            'created_at': snippet['created_at']
        })
    
    # For HTML requests, render the template
    # Ensure rendered_code is always available for display
    rendered_code = snippet['rendered_code'] if snippet['rendered_code'] else snippet['original_code']
    
    # Store this snippet as the last analyzed code in session
    session['last_code_snippet'] = snippet['original_code']
    
    return render_template('index.html',
                         snippet_id=snippet_id,
                         previous_code_snippet=snippet['original_code'],  # Store original for reference
                         rendered_code=rendered_code,
                         show_final_view=True,  # Flag to show fresh input form
                         current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/snippet/<snippet_id>/options', methods=['GET', 'POST'])
def configure_options(snippet_id):
    """Configure dropdown options for a snippet"""
    snippet, options = get_snippet(snippet_id)
    
    if not snippet:
        return jsonify({"error": "Snippet not found"}), 404 if request.is_json else ("Snippet not found", 404)
    
    # For JSON GET requests, return the current options
    if request.method == 'GET' and request.is_json:
        return jsonify({
            'snippet_id': snippet_id,
            'options': options,
            'original_code': snippet['original_code']
        })
    
    if request.method == 'POST':
        # Handle JSON requests
        if request.is_json:
            data = request.get_json()
            action = data.get('action', '')
            
            if action == 'add_option':
                new_option = data.get('new_option', '').strip()
                if new_option and new_option not in options:
                    save_dropdown_option(snippet_id, new_option)
                    options.append(new_option)
                return jsonify({
                    'snippet_id': snippet_id,
                    'options': options,
                    'message': f"Option '{new_option}' added successfully"
                })
            
            elif action == 'remove_option':
                option_to_remove = data.get('option_to_remove', '')
                if option_to_remove in options:
                    remove_dropdown_option(snippet_id, option_to_remove)
                    options.remove(option_to_remove)
                return jsonify({
                    'snippet_id': snippet_id,
                    'options': options,
                    'message': f"Option '{option_to_remove}' removed successfully"
                })
            
            elif action == 'submit_options':
                # Get the latest options
                options = get_dropdown_options(snippet_id)
                
                if options:
                    # Update the code snippet with the new options
                    updated_code = replace_dropdown_placeholder(snippet['original_code'], options)
                    # Save the rendered code to the database
                    update_rendered_code(snippet_id, updated_code)
                    return jsonify({
                        'snippet_id': snippet_id,
                        'rendered_code': updated_code,
                        'message': "Options applied successfully",
                        'view_url': url_for('view_snippet', snippet_id=snippet_id)
                    })
                else:
                    return jsonify({
                        'snippet_id': snippet_id,
                        'rendered_code': snippet['original_code'],
                        'message': "No options to apply",
                        'view_url': url_for('view_snippet', snippet_id=snippet_id)
                    })
            
            elif action == 'skip_options':
                return jsonify({
                    'snippet_id': snippet_id,
                    'rendered_code': snippet['original_code'],
                    'message': "Options skipped",
                    'view_url': url_for('view_snippet', snippet_id=snippet_id)
                })
        
        # Handle form submissions
        else:
            action = request.form.get('action', '')
            
            if action == 'add_option':
                new_option = request.form.get('new_option', '').strip()
                if new_option and new_option not in options:
                    save_dropdown_option(snippet_id, new_option)
                    options.append(new_option)
            
            elif action == 'remove_option':
                option_to_remove = request.form.get('option_to_remove', '')
                if option_to_remove in options:
                    remove_dropdown_option(snippet_id, option_to_remove)
                    options.remove(option_to_remove)
            
            elif action == 'submit_options':
                # Get the latest options
                options = get_dropdown_options(snippet_id)
                
                if options:
                    # Update the code snippet with the new options
                    updated_code = replace_dropdown_placeholder(snippet['original_code'], options)
                    # Save the rendered code to the database
                    update_rendered_code(snippet_id, updated_code)
                    return redirect(url_for('view_snippet', snippet_id=snippet_id))
                else:
                    return redirect(url_for('view_snippet', snippet_id=snippet_id))
            
            elif action == 'skip_options':
                # Save the original code as rendered code when skipping options
                update_rendered_code(snippet_id, snippet['original_code'])
                return redirect(url_for('view_snippet', snippet_id=snippet_id))
    
    # For HTML requests, render the template
    return render_template('index.html',
                         snippet_id=snippet_id,
                         code_snippet=snippet['original_code'],
                         has_dropdowns=True,
                         show_options_form=True,
                         dropdown_options=options,
                         dropdown_detected_message="Dropdown detected",
                         current_date=datetime.now().strftime('%Y-%m-%d'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)