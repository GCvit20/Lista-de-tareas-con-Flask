import functools

from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect
)

from werkzeug.security import check_password_hash, generate_password_hash

from todo.db import get_db

#Creamos un blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST': #Validamos si el metodo utilizado es el de post
        username = request.form['username'] #Sacamos la variable de username del formulari
        password = request.form['password']
        db, c = get_db() #Busca si en la base de datos existe el user y pass solicitados
        error = None #Creamos una variable de error. Si el usuario no envia un user o pass se reemplaza esa variable y se devolvera un mensaje de error
        c.execute( #Ejecutamos la consulta
            'select id from user where username = %s', (username,) #seleccionamos el id para ver si el usuario existe. Si no existe se registra y de lo contrario envia un mensaje de error
        )
        if not username:
            error = 'Username es requerido'
        if not password:
            error = 'Password es requerido'
        elif c.fetchone() is not None:
            error = 'Usuario {} se encuentra registrado.'.format(username)
        if error is None: #De no haber errores se ejecutara la siguiente logica
            c.execute(
                'insert into user (username, password) values (%s, %s)',
                (username, generate_password_hash(password))
            )
            
            db.commit()

            return redirect(url_for('auth.login'))
        flash(error)
    return render_template('auth/register.html') #Esto se retornara si el usuario esta realizando un peticion de get en vez de la de post

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db, c = get_db()
        error=None
        c.execute(
            'select * from user where username = %s', (username,) #Buscamos si el usuario ingresado tiene la misma pass que esta ingresando
        )
        user = c.fetchone() #Sacamos el user de la base de datos

        if user is None:
            error = 'Usuario y/o contraseña invalida'
        elif not check_password_hash(user['password'], password): #Consultamos si el chequeo de la contraseña que se encuentra dentro del usuario, si es que no es la misma que nosotros estamos ingresando
            error = 'Usuario y/o contraseña invalida'
        if error is None:
            session.clear() #limpiamos la sesion 
            session['user_id'] = user['id'] #le asignamos al usuario su id
            return redirect(url_for('todo.index'))
        
        flash(error)
    return render_template('auth/login.html')

#Esta funcion busca el usuario y se lo asigna a g
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id') #Sacamos el user_id del objeto de session

    if user_id is None:
        g.user = None #Si no se encuentra el usuario se le asigna none al mismo ya que no tenemos un usuario que haya iniciado sesion
    else:
        db, c = get_db()
        c.execute(
            'select * from user where id = %s', (user_id,) #buscamos el usuario por su id en la base de datos
        )
        g.user = c.fetchone() #le asignamso el id a g.user


#funcion decoradora recibe como argumento la misma funcion que nosotros estamos decorando. Ej: bp.route
def login_required(view): 
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None: #Si esto se cumple quiere decir que el usuario no inicio sesion
            return redirect(url_for('auth.login')) #redireccionamos al usuario a la pagina de login
        
        return view(**kwargs)
    return wrapped_view


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))