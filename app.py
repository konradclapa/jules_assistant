from flask import Flask, render_template, request

app = Flask(__name__)

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
    return render_template('index.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)