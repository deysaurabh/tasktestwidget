from app import detect_dropdowns, init_db, get_db_connection, save_snippet, get_snippet, save_dropdown_option, get_dropdown_options, update_rendered_code
import sys
import os
import sqlite3

# Use an in-memory database for testing
os.environ['DATABASE_PATH'] = ':memory:'

# Initialize the database
init_db()

# The Amazon Connect widget code snippet with dropdown
code_snippet = """<script type="text/javascript">(function(w, d, x, id){s=d.createElement('script');s.src='https://avp17427.my.gamma.us-west-2.nonprod.connect.aws.a2z.com/connectwidget/static/amazon-connect-chat-interface-client.js';s.async=1;s.id=id;d.getElementsByTagName('head')[0].appendChild(s);w[x] =  w[x] || function() { (w[x].ac = w[x].ac || []).push(arguments) };})(window, document, 'amazon_connect', '2e5ad17d-ad5d-4e55-b7dc-c70d6fd7e2aa');amazon_connect('styles', { headerConfig: { headerMessage: 'How can we help?', headerColorHex: '#123456'}, logoConfig: { sourceUrl: ''} });amazon_connect('snippetId', 'QVFJREFIajlqMGdpeVlnZHNBMlZ1UW82emVGSkpTYXpieW1FczkySVlaUTl0RGRGcEFGRzY0NzVVbFNnWmg5TVdncWw2Qm9aQUFBQWJqQnNCZ2txaGtpRzl3MEJCd2FnWHpCZEFnRUFNRmdHQ1NxR1NJYjNEUUVIQVRBZUJnbGdoa2dCWlFNRUFTNHdFUVFNanAzS0gvUWM0THVOQjBJcUFnRVFnQ3ZIR2d6SDRoQVpId3E3Q3JKVWNrTEdWWitBZm1RWnpoc1dTLzE5aWtmQkY5RTExdjc3R2dXWTJXc2k6OkVEMFBVQ0hpR1c4czdvUjRUOWFUbmlGQVR6V0RYWmJNQU5YeFovN1I1TUZXdWY0NFgxTk5MZFJibDJIaFUwSEF4bGdjYUZ5UHZCNnJZNVA4dE0rMkVsQ05DM3kyZ2VEZHZhb0drbmY2UUowVC9RNGVNTjlKVWwxS2hWQkVubHk0M2pZU0w3b294Y1UrZldHelV0Y0dONElHb1VRQ3NSOD0=');amazon_connect('supportedMessagingContentTypes', [ 'text/plain', 'text/markdown', 'application/vnd.amazonaws.connect.message.interactive', 'application/vnd.amazonaws.connect.message.interactive.response' ]);amazon_connect('displayType', 'EMBEDDED_INLINE');amazon_connect('viewConfig', '{\"name\":\"TaskDemoWidget\",\"id\":\"92bb4fe2-3e40-4e60-ac01-1ccc8f95ae9b\",\"arn\":\"arn:aws:connect:us-west-2:365970984240:instance/d8ea86ee-52a9-4853-92f7-2f83d7eb887b/view/92bb4fe2-3e40-4e60-ac01-1ccc8f95ae9b:$LATEST\",\"type\":\"CUSTOMER_MANAGED\",\"content\":{\"template\":{\"Head\":{\"Configuration\":{\"Layout\":{\"Columns\":[12]}},\"Title\":\"TaskDemoWidget\"},\"Body\":[{\"_id\":\"Form_1752529870553\",\"Type\":\"Form\",\"Props\":{\"HideBorder\":false},\"Content\":[{\"_id\":\"Dropdown_1752529883497\",\"Type\":\"Dropdown\",\"Props\":{\"Label\":\"Work Queue\",\"Name\":\"input-1\",\"DefaultValue\":[\"Option 1\"],\"Options\":[{\"Label\":\"CCS_ACH_Back_End_PRC\",\"Value\":\"CCS_ACH_Back_End_PRC\"},{\"Label\":\"CCS_ACH_Front_End_PRC\",\"Value\":\"CCS_ACH_Front_End_PRC\"},{\"Label\":\"CCS_ATM_PRC\",\"Value\":\"CCS_ATM_PRC\"},{\"Label\":\"CCS_Approvals_PRC\",\"Value\":\"CCS_Approvals_PRC\"}],\"MultiSelect\":false,\"Clearable\":false,\"Required\":true},\"Content\":[]},{\"_id\":\"ConnectAction_1752529906788\",\"Type\":\"ConnectAction\",\"Props\":{\"ConnectActionType\":\"StartTaskContact\",\"Label\":\"Create Task\",\"StartTaskContactProps\":{\"ContactFlowId\":\"arn:aws:connect:us-west-2:365970984240:instance/d8ea86ee-52a9-4853-92f7-2f83d7eb887b/contact-flow/fb5460bd-26ee-4a21-aaf1-ee11b3184f3b\",\"TaskFields\":{\"Name\":\"WidgetTask\",\"References\":{\"Notes\":{\"Type\":\"STRING\",\"Value\":\"Notes\"}},\"Description\":\"This is a self assigned manual task\"},\"Attributes\":[{\"Key\":\"WorkQueue\",\"Value\":{\"_linkedFormOutputName\":\"input-1\"}}],\"TaskTemplateId\":\"arn:aws:connect:us-west-2:365970984240:instance/d8ea86ee-52a9-4853-92f7-2f83d7eb887b/task-template/55fa5225-4103-4e9d-a10f-75e9919c20ac\"},\"StartEmailContactProps\":{\"DestinationEmailAddress\":\"\",\"ContactFlowId\":\"\",\"EmailFields\":{\"CustomerDisplayName\":\"\",\"CustomerEmailAddress\":\"\",\"Subject\":\"\",\"Body\":\"\"},\"Attributes\":[{\"Key\":\"\",\"Value\":\"\"}]},\"StartChatContactProps\":{\"ContactFlowId\":\"\",\"ChatFields\":{\"CustomerDisplayName\":\"\",\"InitialMessage\":\"\"},\"Attributes\":[{\"Key\":\"\",\"Value\":\"\"}]}},\"Content\":[\"Connect Action Button\"]}]}]},\"actions\":[\"ActionSelected\"],\"inputSchema\":{\"type\":\"object\",\"properties\":{},\"required\":[],\"$defs\":{\"ViewCondition\":{\"$id\":\"/view/condition\",\"type\":\"object\",\"patternProperties\":{\"^(MoreThan|LessThan|NotEqual|Equal|Include)$\":{\"type\":\"object\",\"properties\":{\"ElementByKey\":{\"type\":\"string\"},\"ElementByValue\":{\"anyOf\":[{\"type\":\"number\"},{\"type\":\"string\"}]}},\"additionalProperties\":false},\"^(AndConditions|OrConditions)$\":{\"type\":\"array\",\"items\":{\"$ref\":\"/view/condition\"}}},\"additionalProperties\":false}}}},\"status\":\"PUBLISHED\",\"viewContentSha256\":\"bff263c0ab706750a2bd96a364019fcbb5a5bbbc1ac3639e9d5d88942a99684c\"}');</script>"""

print("Testing dropdown detection...")
result = detect_dropdowns(code_snippet)
print(f"Detection result: {result}")

if result:
    print("✅ Test passed: Dropdown detected successfully!")
    
    # Test database operations
    print("\nTesting database operations...")
    
    # Save snippet to database
    snippet_id = save_snippet(code_snippet, has_dropdowns=True)
    print(f"Saved snippet with ID: {snippet_id}")
    
    # Retrieve snippet from database
    snippet, options = get_snippet(snippet_id)
    print(f"Retrieved snippet: {snippet['id'] == snippet_id}")
    
    # Add options
    test_options = ["Option A", "Option B", "Option C"]
    for option in test_options:
        save_dropdown_option(snippet_id, option)
    
    # Get options
    saved_options = get_dropdown_options(snippet_id)
    print(f"Saved options: {saved_options}")
    
    if set(test_options) == set(saved_options):
        print("✅ Test passed: Options saved and retrieved successfully!")
    else:
        print("❌ Test failed: Options not saved or retrieved correctly!")
        sys.exit(1)
    
    # Update rendered code
    rendered_code = "Test rendered code with options: " + ", ".join(test_options)
    update_rendered_code(snippet_id, rendered_code)
    
    # Verify rendered code was updated
    updated_snippet, _ = get_snippet(snippet_id)
    if updated_snippet['rendered_code'] == rendered_code:
        print("✅ Test passed: Rendered code updated successfully!")
    else:
        print("❌ Test failed: Rendered code not updated correctly!")
        sys.exit(1)
    
    print("\nAll database tests passed!")
else:
    print("❌ Test failed: Dropdown not detected!")
    sys.exit(1)