from flask import Flask, render_template, request, redirect, url_for, session
import os

template_dir = os.path.abspath('../../Module/Views')
static_dir = os.path.abspath('../../Module')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'tu_clave_secreta'

app.secret_key = 'clave_secreta_segura'

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['username']
        clave = request.form['password']
        if usuario == 'admin' and clave == '1234':
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            error = 'Credenciales incorrectas'
    return render_template('login.html', error=error)

@app.route('/')
def index():
    if 'usuario' in session:
        return render_template('index.html', usuario=session['usuario'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
