from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__,
            template_folder='../../module/views',
            static_folder='../../module')

# Ruta principal
@app.route('/')
def index():
    return render_template('login.html')

# Servir CSS
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

# Servir JS
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

# Servir imagen
@app.route('/views/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(app.static_folder, 'views'), filename)

if __name__ == '__main__':
    app.run(debug=True)
