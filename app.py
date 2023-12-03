from flask import g, Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'kibo'

DATABASE = 'tasks.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_table():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task_name TEXT NOT NULL,
            task_description TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()

create_table()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def user():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
                conn.commit()
            flash(f'User {username} created successfully!', 'success')
            return redirect(url_for('home', user=username))
        except sqlite3.IntegrityError:
            error = f"User '{username}' already exists. Please choose a different username."
            flash(error, 'error')
    return render_template('user.html', error=error)


@app.route('/<user>', methods=['GET'])
def home(user):
    return render_template('home.html', user=user)

@app.route('/users', methods=['GET'])
def users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
    return render_template('users.html', users=users)

@app.route('/<user>/tasks', methods=['GET'])
def list_tasks(user):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE user_id = (SELECT id FROM users WHERE username = ?)', (user,))
    tasks = cursor.fetchall()
    return render_template('list_tasks.html', tasks=tasks, user=user)

@app.route('/<user>/tasks/<int:task_id>', methods=['GET'])
def view_task(user, task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ? AND user_id = (SELECT id FROM users WHERE username = ?)', (task_id, user))
    task = cursor.fetchone()
    return render_template('view_task.html', task=task, user=user)

@app.route('/<user>/tasks/new', methods=['GET', 'POST'])
def new_task(user):
    if request.method == 'POST':
        task_name = request.form['task_name']
        task_description = request.form['task_description']

        conn = get_db()
        cursor = conn.cursor()

        # Get the user_id based on the provided username
        cursor.execute('SELECT id FROM users WHERE username = ?', (user,))
        user_id = cursor.fetchone()

        if user_id:
            cursor.execute('''
                INSERT INTO tasks (task_name, task_description, user_id)
                VALUES (?, ?, ?)
            ''', (task_name, task_description, user_id[0]))

            conn.commit()
            return redirect(url_for('list_tasks', user=user))
    
    return render_template('new_task.html', user=user)

@app.route('/<user>/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(user, task_id):
    if request.method == 'POST':
        task_name = request.form['task_name']
        task_description = request.form['task_description']

        conn = get_db()
        cursor = conn.cursor()

        # Update the task based on task_id
        cursor.execute('''
            UPDATE tasks SET task_name = ?, task_description = ? WHERE id = ? AND user_id = (
                SELECT id FROM users WHERE username = ?
            )
        ''', (task_name, task_description, task_id, user))

        conn.commit()
        return redirect(url_for('list_tasks', user=user))

    else:
        # Fetch task details for displaying in the edit form
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM tasks WHERE id = ? AND user_id = (
                SELECT id FROM users WHERE username = ?
            )
        ''', (task_id, user))
        task = cursor.fetchone()

        if task:
            return render_template('edit_task.html', user=user, task=task)
        else:
            return redirect(url_for('list_tasks', user=user))
        

@app.route('/<user>/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(user, task_id):
    conn = get_db()
    cursor = conn.cursor()

    # Delete the task based on task_id
    cursor.execute('''
        DELETE FROM tasks WHERE id = ? AND user_id = (
            SELECT id FROM users WHERE username = ?
        )
    ''', (task_id, user))

    conn.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('list_tasks', user=user))


if __name__ == '__main__':
    app.run(debug=True)



















