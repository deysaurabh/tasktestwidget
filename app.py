from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    code_snippet = ""
    if request.method == 'POST':
        code_snippet = request.form.get('code', '')
    return render_template('index.html', code_snippet=code_snippet, current_date=datetime.now().strftime('%Y-%m-%d'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)