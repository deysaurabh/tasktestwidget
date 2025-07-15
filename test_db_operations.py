import unittest
import os
import sqlite3
from app import detect_dropdowns

class TestDatabaseOperations(unittest.TestCase):
    
    def setUp(self):
        # Use a test database file
        self.test_db_path = 'test_snippets.db'
        
        # Create the test database
        self.conn = sqlite3.connect(self.test_db_path)
        self.cursor = self.conn.cursor()
        
        # Create snippets table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS snippets (
            id TEXT PRIMARY KEY,
            original_code TEXT NOT NULL,
            rendered_code TEXT,
            has_dropdowns BOOLEAN NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create dropdown_options table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS dropdown_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snippet_id TEXT NOT NULL,
            option_text TEXT NOT NULL,
            FOREIGN KEY (snippet_id) REFERENCES snippets (id)
        )
        ''')
        
        self.conn.commit()
        
        # The Amazon Connect widget code snippet with dropdown
        self.code_snippet = """<script type="text/javascript">amazon_connect('viewConfig', '{\"content\":{\"template\":{\"Body\":[{\"Content\":[{\"_id\":\"Dropdown_1752529883497\",\"Type\":\"Dropdown\",\"Props\":{\"Label\":\"Work Queue\",\"Options\":[{\"Label\":\"CCS_ACH_Back_End_PRC\",\"Value\":\"CCS_ACH_Back_End_PRC\"},{\"Label\":\"CCS_ACH_Front_End_PRC\",\"Value\":\"CCS_ACH_Front_End_PRC\"}]}}]}]}}}');</script>"""
    
    def tearDown(self):
        # Close the database connection
        self.conn.close()
        
        # Remove the test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_detect_dropdowns(self):
        """Test the detect_dropdowns function with the code snippet"""
        result = detect_dropdowns(self.code_snippet)
        self.assertTrue(result, "Should detect dropdown in the code snippet")
    
    def test_save_and_retrieve_snippet(self):
        """Test saving and retrieving a snippet from the database"""
        # Save a snippet
        snippet_id = "test-snippet-id"
        self.cursor.execute(
            'INSERT INTO snippets (id, original_code, has_dropdowns) VALUES (?, ?, ?)',
            (snippet_id, self.code_snippet, True)
        )
        self.conn.commit()
        
        # Retrieve the snippet
        self.cursor.execute('SELECT * FROM snippets WHERE id = ?', (snippet_id,))
        snippet = self.cursor.fetchone()
        
        self.assertIsNotNone(snippet, "Snippet should be saved in the database")
        self.assertEqual(snippet[0], snippet_id, "Snippet ID should match")
        self.assertEqual(snippet[1], self.code_snippet, "Original code should match")
        self.assertTrue(snippet[3], "has_dropdowns should be True")
    
    def test_save_and_retrieve_options(self):
        """Test saving and retrieving dropdown options"""
        # Save a snippet
        snippet_id = "test-snippet-id"
        self.cursor.execute(
            'INSERT INTO snippets (id, original_code, has_dropdowns) VALUES (?, ?, ?)',
            (snippet_id, self.code_snippet, True)
        )
        
        # Save options
        test_options = ["Option A", "Option B", "Option C"]
        for option in test_options:
            self.cursor.execute(
                'INSERT INTO dropdown_options (snippet_id, option_text) VALUES (?, ?)',
                (snippet_id, option)
            )
        
        self.conn.commit()
        
        # Retrieve options
        self.cursor.execute('SELECT option_text FROM dropdown_options WHERE snippet_id = ?', (snippet_id,))
        options = [row[0] for row in self.cursor.fetchall()]
        
        self.assertEqual(len(options), len(test_options), "Should have the same number of options")
        for option in test_options:
            self.assertIn(option, options, f"Option '{option}' should be in the retrieved options")
    
    def test_update_rendered_code(self):
        """Test updating the rendered code for a snippet"""
        # Save a snippet
        snippet_id = "test-snippet-id"
        self.cursor.execute(
            'INSERT INTO snippets (id, original_code, has_dropdowns) VALUES (?, ?, ?)',
            (snippet_id, self.code_snippet, True)
        )
        
        # Update rendered code
        rendered_code = "Test rendered code"
        self.cursor.execute(
            'UPDATE snippets SET rendered_code = ? WHERE id = ?',
            (rendered_code, snippet_id)
        )
        
        self.conn.commit()
        
        # Retrieve the snippet
        self.cursor.execute('SELECT rendered_code FROM snippets WHERE id = ?', (snippet_id,))
        result = self.cursor.fetchone()
        
        self.assertEqual(result[0], rendered_code, "Rendered code should be updated")

if __name__ == '__main__':
    unittest.main()