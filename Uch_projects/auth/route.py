import os
from flask import Blueprint, render_template, request, redirect, session
from auth.model_route import model_route
from database.sql_provider import SQLProvider

blueprint_auth = Blueprint(
    'blueprint_auth',
    __name__,
    template_folder='templates'
)

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

@blueprint_auth.route('/', methods=["GET","POST"])
def auth_index():
    if request.method == 'GET':
        return render_template('auth_index.html')
    else:
        user_input = request.form
        result_info = model_route(provider, user_input,'internal.sql')
        if result_info.status:
            results = result_info.result
            session['user_id']=results[0]['user_id']
            session['user_group'] = results[0]['user_group']
            session.permanent = True
            return redirect('/')
        else:
                return render_template("auth_err.html")

@blueprint_auth.route('/exit', methods=["GET"])
def auth_exit():
    return render_template('auth_exit.html')