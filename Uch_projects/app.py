import json
from flask import Flask, render_template, session, redirect
from access import login_required
from query.route import blueprint_query
from auth.route import blueprint_auth
from report.route import blueprint_report
from order.route import blueprint_order

app = Flask(__name__)
app.secret_key = 'You will never guess'

with open("data/db_config.json") as f:
    app.config['db_config'] = json.load(f)
with open("data/access.json") as f:
    app.config['db_access'] = json.load(f)

app.register_blueprint(blueprint_query, url_prefix='/query')
app.register_blueprint(blueprint_auth, url_prefix='/auth')
app.register_blueprint(blueprint_report, url_prefix='/report')
app.register_blueprint(blueprint_order, url_prefix='/order')

@app.route('/', methods=["GET"])
@login_required
def main_menu():
    return render_template("main_menu.html")

@app.route('/exit', methods=["GET"])
def exit():
    session.pop('user_id', None)
    session.pop('user_group', None)
    return redirect('/auth')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)