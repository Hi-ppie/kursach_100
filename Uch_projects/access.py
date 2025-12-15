from functools import wraps
from flask import session, redirect, url_for, current_app, request, render_template


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_group' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('blueprint_auth.auth_index'))
    return wrapper

def group_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_group' in session:
            access = current_app.config['db_access']
            user_request = request.endpoint.split('.')[0]
            user_role = session.get('user_group')
            if user_role in access and user_request in access[user_role]:
                return func(*args, **kwargs)
            else:
                return render_template('auth_close.html')
        return redirect(url_for('blueprint_auth.auth_index'))
    return wrapper
