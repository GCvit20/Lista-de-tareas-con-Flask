from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort
from todo.auth import login_required
from todo.db import get_db

bp = Blueprint('todo', __name__)

@bp.route('/')
@login_required #llamamos la funcion para proteger la funcion de index
def index():
    db, c = get_db()
    c.execute(
        'select t.id, t.description, u.username, t.completed, t.created_at from todo t JOIN user ' 
        'u on t.created_by = u.id where t.created_by = %s order by created_at desc', (g.user['id'],) #t hace referencia al alias que le asignamos a la tabla de 'todo'. U es el alias que le asignamos a la tabla de usuario y luego debemos indicar donde queremos que los usuario sean agregados al resultado de la cosulta (t.created_by). El id del usuario debe ser igual al atributo de created by de la tabla de 'todo'. Luego ordenamos descendientemente 
    )

    todos = c.fetchall() #le indicamos al cursor que nos traiga todos los datos

    return render_template('todo/index.html', todos=todos) #creamos una plantilla que se encontrara dentro de la carpeta de 'todo' y le pasaremos los 'todo' a esta plantilla

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST': #Si es que estamos utilizando el metodo de post se ejecura la instruccion
        description = request.form['description'] #Sacamos la descripcion 
        error = None #Mensaje de error

        if not description: #Si no existe una descripcion
            error = 'Descripción es requerida'
        
        if error is not None: #Si el error no es 'None' enviamos un mensaje flash
            flash(error)
        else: #En el caso de que nuestro mensaje de error se encuentre vacio o siga siendo None se ejecutara la siguiente instruccion y se creara nuestro 'todo'
            db, c = get_db()
            c.execute (
                'insert into todo (description, completed, created_by)' #Le pasamos los parametros que queremos insertar
                ' values (%s,%s,%s)', #Le indicamos los valores que queremos incluir
                (description, False, g.user['id']) #Le pasamos como primer elemento de nuestra tupla la descripcion, luego el estado (si se encuentra completado o no) y por ultimo el id del usuario en contexto  
            )

            db.commit()

            return redirect(url_for('todo.index'))
        
    return render_template('todo/create.html')


def get_todo(id):
    db, c = get_db()
    c.execute(
        'select t.id, t.description, t.completed, t.created_by, t.created_at, u.username' 
        ' from todo t join user u on t.created_by = u.id where t.id = %s', (id,)
    )

    todo = c.fetchone() #Neceitamos traer solo un dato que en este caso es el id

    if todo is None:
        abort(404, "El todo de is {0} no existe".format(id)) 
    
    return todo

@bp.route('/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
    todo = get_todo(id)

    if request.method == 'POST':
        description = request.form['description']
        completed = True if request.form.get('completd') == 'on' else False #Checkbox
        error = None

        if not description: #Validacion
            error= 'La descripción es requerida'
        
        if error is not None: #Validacion
            flash(error)
        else:
            db, c = get_db()

            c.execute(
                'update todo set description = %s, completed = %s where id = %s and created_by = %s',
                (description, completed, id, g.user['id'])
            )

            db.commit()
            return redirect(url_for('todo.index'))

    return render_template('todo/update.html', todo=todo)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db, c = get_db()

    c.execute('delete from todo where id = %s and created_by = %s', (id, g.user['id']))
    db.commit()
    return redirect(url_for('todo.index'))