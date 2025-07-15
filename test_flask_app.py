import unittest
import io
import os
import sqlite3
from contextlib import redirect_stdout
from app import app, detect_dropdowns, init_db, get_db_connection

class TestFlaskApp(unittest.TestCase):
    
    def setUp(self):
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Use an in-memory database for testing
        app.config['DATABASE_PATH'] = ':memory:'
        
        # Initialize the test client
        self.client = app.test_client()
        
        # Create a test context
        with app.app_context():
            # Initialize the in-memory database
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
        
        # The Amazon Connect widget code snippet with dropdown
        self.code_snippet = """<script type="text/javascript">(function(w, d, x, id){s=d.createElement('script');s.src='https://avp17427.my.gamma.us-west-2.nonprod.connect.aws.a2z.com/connectwidget/static/amazon-connect-chat-interface-client.js';s.async=1;s.id=id;d.getElementsByTagName('head')[0].appendChild(s);w[x] =  w[x] || function() { (w[x].ac = w[x].ac || []).push(arguments) };})(window, document, 'amazon_connect', '2e5ad17d-ad5d-4e55-b7dc-c70d6fd7e2aa');amazon_connect('styles', { headerConfig: { headerMessage: 'How can we help?', headerColorHex: '#123456'}, logoConfig: { sourceUrl: ''} });amazon_connect('snippetId', 'QVFJREFIajlqMGdpeVlnZHNBMlZ1UW82emVGSkpTYXpieW1FczkySVlaUTl0RGRGcEFGRzY0NzVVbFNnWmg5TVdncWw2Qm9aQUFBQWJqQnNCZ2txaGtpRzl3MEJCd2FnWHpCZEFnRUFNRmdHQ1NxR1NJYjNEUUVIQVRBZUJnbGdoa2dCWlFNRUFTNHdFUVFNanAzS0gvUWM0THVOQjBJcUFnRVFnQ3ZIR2d6SDRoQVpId3E3Q3JKVWNrTEdWWitBZm1RWnpoc1dTLzE5aWtmQkY5RTExdjc3R2dXWTJXc2k6OkVEMFBVQ0hpR1c4czdvUjRUOWFUbmlGQVR6V0RYWmJNQU5YeFovN1I1TUZXdWY0NFgxTk5MZFJibDJIaFUwSEF4bGdjYUZ5UHZCNnJZNVA4dE0rMkVsQ05DM3kyZ2VEZHZhb0drbmY2UUowVC9RNGVNTjlKVWwxS2hWQkVubHk0M2pZU0w3b294Y1UrZldHelV0Y0dONElHb1VRQ3NSOD0=');amazon_connect('supportedMessagingContentTypes', [ 'text/plain', 'text/markdown', 'application/vnd.amazonaws.connect.message.interactive', 'application/vnd.amazonaws.connect.message.interactive.response' ]);amazon_connect('displayType', 'EMBEDDED_INLINE');amazon_connect('viewConfig', '{\"name\":\"TaskDemoWidget\",\"id\":\"92bb4fe2-3e40-4e60-ac01-1ccc8f95ae9b\",\"arn\":\"arn:aws:connect:us-west-2:365970984240:instance/d8ea86ee-52a9-4853-92f7-2f83d7eb887b/view/92bb4fe2-3e40-4e60-ac01-1ccc8f95ae9b:$LATEST\",\"type\":\"CUSTOMER_MANAGED\",\"content\":{\"template\":{\"Head\":{\"Configuration\":{\"Layout\":{\"Columns\":[12]}},\"Title\":\"TaskDemoWidget\"},\"Body\":[{\"_id\":\"Form_1752529870553\",\"Type\":\"Form\",\"Props\":{\"HideBorder\":false},\"Content\":[{\"_id\":\"Dropdown_1752529883497\",\"Type\":\"Dropdown\",\"Props\":{\"Label\":\"Work Queue\",\"Name\":\"input-1\",\"DefaultValue\":[\"Option 1\"],\"Options\":[{\"Label\":\"CCS_ACH_Back_End_PRC\",\"Value\":\"CCS_ACH_Back_End_PRC\"},{\"Label\":\"CCS_ACH_Front_End_PRC\",\"Value\":\"CCS_ACH_Front_End_PRC\"},{\"Label\":\"CCS_ATM_PRC\",\"Value\":\"CCS_ATM_PRC\"},{\"Label\":\"CCS_Approvals_PRC\",\"Value\":\"CCS_Approvals_PRC\"}],\"MultiSelect\":false,\"Clearable\":false,\"Required\":true},\"Content\":[]},{\"_id\":\"ConnectAction_1752529906788\",\"Type\":\"ConnectAction\",\"Props\":{\"ConnectActionType\":\"StartTaskContact\",\"Label\":\"Create Task\",\"StartTaskContactProps\":{\"ContactFlowId\":\"arn:aws:connect:us-west-2:365970984240:instance/d8ea86ee-52a9-4853-92f7-2f83d7eb887b/contact-flow/fb5460bd-26ee-4a21-aaf1-ee11b3184f3b\",\"TaskFields\":{\"Name\":\"WidgetTask\",\"References\":{\"Notes\":{\"Type\":\"STRING\",\"Value\":\"Notes\"}},\"Description\":\"This is a self assigned manual task\"},\"Attributes\":[{\"Key\":\"WorkQueue\",\"Value\":{\"_linkedFormOutputName\":\"input-1\"}}],\"TaskTemplateId\":\"arn:aws:connect:us-west-2:365970984240:instance/d8ea86ee-52a9-4853-92f7-2f83d7eb887b/task-template/55fa5225-4103-4e9d-a10f-75e9919c20ac\"},\"StartEmailContactProps\":{\"DestinationEmailAddress\":\"\",\"ContactFlowId\":\"\",\"EmailFields\":{\"CustomerDisplayName\":\"\",\"CustomerEmailAddress\":\"\",\"Subject\":\"\",\"Body\":\"\"},\"Attributes\":[{\"Key\":\"\",\"Value\":\"\"}]},\"StartChatContactProps\":{\"ContactFlowId\":\"\",\"ChatFields\":{\"CustomerDisplayName\":\"\",\"InitialMessage\":\"\"},\"Attributes\":[{\"Key\":\"\",\"Value\":\"\"}]}},\"Content\":[\"Connect Action Button\"]}]}]},\"actions\":[\"ActionSelected\"],\"inputSchema\":{\"type\":\"object\",\"properties\":{},\"required\":[],\"$defs\":{\"ViewCondition\":{\"$id\":\"/view/condition\",\"type\":\"object\",\"patternProperties\":{\"^(MoreThan|LessThan|NotEqual|Equal|Include)$\":{\"type\":\"object\",\"properties\":{\"ElementByKey\":{\"type\":\"string\"},\"ElementByValue\":{\"anyOf\":[{\"type\":\"number\"},{\"type\":\"string\"}]}},\"additionalProperties\":false},\"^(AndConditions|OrConditions)$\":{\"type\":\"array\",\"items\":{\"$ref\":\"/view/condition\"}}},\"additionalProperties\":false}}}},\"status\":\"PUBLISHED\",\"viewContentSha256\":\"bff263c0ab706750a2bd96a364019fcbb5a5bbbc1ac3639e9d5d88942a99684c\"}');</script>"""
    
    def test_detect_dropdowns_function(self):
        """Test the detect_dropdowns function directly"""
        # Capture stdout to verify "Dropdown detected" is printed
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = detect_dropdowns(self.code_snippet)
        
        # Check function return value
        self.assertTrue(result, "Should detect dropdown in the code snippet")
        
        # Check console output
        console_output = captured_output.getvalue()
        self.assertIn("Dropdown detected with pattern", console_output, 
                     "Should print 'Dropdown detected with pattern' to console")
    
    def test_analyze_code_endpoint(self):
        """Test the Flask app's analyze_code endpoint with the dropdown snippet"""
        # Capture stdout to verify "Dropdown detected" is printed
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            response = self.client.post('/analyze', data={
                'code': self.code_snippet
            }, follow_redirects=True)
        
        # Check response status
        self.assertEqual(response.status_code, 200, "Response should be successful")
        
        # Check console output
        console_output = captured_output.getvalue()
        self.assertIn("Dropdown detected", console_output, 
                     "Should print 'Dropdown detected' to console")
        
        # Check that the response contains the dropdown configuration form
        self.assertIn("Dropdown Detected!", response.data.decode('utf-8'),
                     "Response should contain 'Dropdown Detected!' message")
    
    def test_database_operations(self):
        """Test database operations for snippets and options"""
        # Submit a code snippet
        response = self.client.post('/analyze', data={
            'code': self.code_snippet
        }, follow_redirects=True)
        
        # Extract the snippet_id from the response URL
        snippet_id = response.request.path.split('/')[-1]
        
        # Check that the snippet was saved to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM snippets WHERE id = ?', (snippet_id,))
        snippet = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(snippet, "Snippet should be saved in the database")
        self.assertEqual(snippet['original_code'], self.code_snippet, 
                        "Original code should match the submitted code")
        self.assertTrue(snippet['has_dropdowns'], 
                       "has_dropdowns should be True for this snippet")
        
        # Add a dropdown option
        test_option = "Test Option 1"
        response = self.client.post(f'/snippet/{snippet_id}/options', data={
            'action': 'add_option',
            'new_option': test_option
        })
        
        # Check that the option was saved to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM dropdown_options WHERE snippet_id = ?', (snippet_id,))
        options = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(options), 1, "Should have one option saved")
        self.assertEqual(options[0]['option_text'], test_option, 
                        "Option text should match the submitted option")
        
        # Submit the options and check that the rendered code is updated
        response = self.client.post(f'/snippet/{snippet_id}/options', data={
            'action': 'submit_options'
        }, follow_redirects=True)
        
        # Check that the rendered code was updated in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT rendered_code FROM snippets WHERE id = ?', (snippet_id,))
        rendered_code = cursor.fetchone()['rendered_code']
        conn.close()
        
        self.assertIsNotNone(rendered_code, "Rendered code should not be None")
        self.assertIn(test_option, rendered_code, 
                     "Rendered code should contain the added option")

if __name__ == '__main__':
    print("Running Flask app tests...")
    unittest.main()