import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

app.config.setdefault('THEME_CONFIG_FILE', 'theme_config.json')

def get_current_theme():
    try:
        with open(app.config['THEME_CONFIG_FILE'], 'r') as f:
            config = json.load(f)
            return config.get('theme', 'light')
    except (FileNotFoundError, json.JSONDecodeError):
        # If file not found or JSON is invalid, default to 'light' and recreate the file.
        # Need to ensure app context for set_current_theme if called from here,
        # or pass app explicitly. For simplicity, we assume app context is available.
        set_current_theme('light')
        return 'light'

def set_current_theme(theme_name):
    with open(app.config['THEME_CONFIG_FILE'], 'w') as f:
        json.dump({'theme': theme_name}, f)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'button1' in request.form:
            message = "Button 1 was clicked!"
        elif 'button2' in request.form:
            message = "Button 2 was clicked!"
        else:
            message = "An unknown button was clicked!" # Should not happen with current setup
    else:
        message = "Please click a button."
    current_theme = get_current_theme()
    return render_template('index.html', message=message, current_theme=current_theme)

@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    current_theme = get_current_theme()
    new_theme = 'dark' if current_theme == 'light' else 'light'
    set_current_theme(new_theme)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)