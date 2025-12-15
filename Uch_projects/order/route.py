import os
from flask import Blueprint, render_template, request, session, redirect, url_for
from order.model_route import model_route, model_route_add, model_route_insert, model_route_delete, load_basket_from_db
from database.sql_provider import SQLProvider
from access import group_required

blueprint_order = Blueprint(
    'blueprint_order',
    __name__,
    template_folder='templates'
)

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

@blueprint_order.route('/client', methods=["GET","POST"])
@group_required
def client():
    if request.method == "POST":
        user_input = request.form
        session['record_book_num'] = user_input['record_book_num']
        result_info = model_route(provider, user_input, 'client.sql')
        if result_info.status:
            session['Cl_id'] = result_info.result[0]['student_id']
            return redirect(url_for('blueprint_order.order_index'))
        else:
            return render_template('client_notfound.html',record_book_num=user_input['record_book_num'])
    else:
        return render_template("client.html")

@blueprint_order.route('/', methods=["GET"])
@group_required
def order_index():
    if 'Cl_id' not in session:
        return redirect(url_for('blueprint_order.client'))
    if 'project_id' in session:
        user_input = {}
        result_info = model_route(provider, user_input, 'teachers.sql')
    else:
        user_input = {'student_id': session['Cl_id']}
        result_info = model_route(provider, user_input, 'books.sql')
    items = result_info.result
    basket = session.get('basket')
    for item in items:
        if 'teacher_number' in item:
            item['amount'] = item['teacher_number']
            if basket:
                for key in basket:
                    if int(key) == item['teacher_id']:
                        item['amount'] = 0
                        break
    return render_template("basket_order_list.html", items=items, basket=basket)

@blueprint_order.route('/add', methods=["POST"])
@group_required
def add_index():
    user_input = request.form
    if 'action' in user_input and user_input['action'] in ['Назначить', 'Изменить']:
        session['project_id'] = user_input['project_id']
        session['defense_date'] = user_input['defense_date']
        session['mode'] = 'edit' if user_input['action'] == 'Изменить' else 'create'
        if session['mode'] == 'edit':
            load_basket_from_db(provider, session['project_id'])
        return redirect(url_for('blueprint_order.order_index'))
    else:
        result_status = model_route_add(provider, user_input, 'book.sql')
        if result_status:
            return redirect(url_for('blueprint_order.order_index'))
        else:
            return render_template("basket_err.html",error="добавлении преподавателя в комиссию")

@blueprint_order.route('/delete', methods=["POST"])
@group_required
def delete_commission():
    user_input = request.form
    model_route_delete(provider, user_input)
    return render_template("delete_success.html")

@blueprint_order.route('/clear', methods=["GET"])
@group_required
def clear_basket():
    if 'basket' in session:
        session.pop('basket')
    return redirect(url_for('blueprint_order.order_index'))

@blueprint_order.route('/save', methods=["GET"])
@group_required
def save_order():
    if 'basket' in session and 'project_id' in session:
        if session.get('mode') == 'edit':
            model_route_delete(provider, {'project_id': session['project_id']})
        o_id = model_route_insert(provider, 'insert_o.sql', 'insert_ol.sql','teachers.sql')
        if o_id:
            session.pop('basket')
            session.pop('project_id')
            session.pop('defense_date')
            session.pop('mode', None)
            return render_template("save_success.html")
        else:
            return render_template("basket_err.html",error="формировании комиссии")
    else:
        return redirect(url_for('blueprint_order.order_index'))

@blueprint_order.route('/exit', methods=["GET"])
@group_required
def exit():
    if 'Cl_id' in session:
        session.pop('Cl_id')
    if 'record_book_num' in session:
        session.pop('record_book_num')
    if 'basket' in session:
        session.pop('basket')
    if 'project_id' in session:
        session.pop('project_id')
    if 'defense_date' in session:
        session.pop('defense_date')
    if 'mode' in session:
        session.pop('mode')
    return redirect('/')
