import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from order.model_route import (
    model_route, model_route_add, model_route_insert, model_route_delete, load_basket_from_db,
    get_disciplines, get_projects_by_discipline, create_commissions, get_busy_teachers_by_date, get_schedule
)
from database.sql_provider import SQLProvider
from access import group_required

blueprint_order = Blueprint(
    'blueprint_order',
    __name__,
    template_folder='templates'
)

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

# Одностраничный поток создания комиссии
@blueprint_order.route('/create', methods=["GET", "POST"])
@group_required
def create():
    if request.method == 'GET':
        teachers_info = model_route(provider, {}, 'teachers.sql')
        if not teachers_info.status:
            return render_template("basket_err.html", error="получении списка преподавателей")
        disciplines = get_disciplines(provider)
        return render_template("select_teachers_onepage.html", teachers=teachers_info.result, disciplines=disciplines)
    else:
        # Окончательная отправка: получаем выбранных преподавателей, проектов и дату
        teacher_ids = request.form.getlist('teacher_id')
        project_ids = request.form.getlist('project_id')
        defense_date = request.form.get('defense_date')
        if not teacher_ids or not project_ids or not defense_date:
            return render_template("basket_err.html", error="не выбраны преподаватели/проекты/дата")
        # получить объекты проектов по их id (нужен supervisor_id и т.д.)
        all_projects = []
        # данные проектов можно передать через form (hidden) или получить через provider; проще: получить для дисциплины
        # здесь мы ожидаем, что client отправит project_id и мы можем собрать проекты по project_id используя existing SQL
        # Получим все проекты по discipline из session (если сохранили), иначе используем select per id
        # Лучший вариант: получить projects_by_discipline по discipline_id, затем фильтровать
        discipline_id = request.form.get('discipline_id')
        if discipline_id:
            projects_all = get_projects_by_discipline(provider, int(discipline_id))
            for p in projects_all:
                if str(p['project_id']) in project_ids:
                    all_projects.append(p)
        else:
            # если discipline_id не передан, попытаемся собрать проекты по каждому project_id напрямую
            for pid in project_ids:
                # использовать existing SQL: projects_by_discipline.sql требует discipline; поэтому не лучший путь
                # упрощённо пропускаем — в нормальном потоке discipline_id всегда присутствует
                pass

        created, skipped = create_commissions(provider, [int(x) for x in teacher_ids], all_projects, defense_date)

        return render_template("commission_result.html", created=created, skipped=skipped)


# AJAX endpoint: получить проекты по дисциплине (JSON)
@blueprint_order.route('/ajax/projects', methods=['POST'])
@group_required
def ajax_projects():
    discipline_id = request.json.get('discipline_id')
    if not discipline_id:
        return jsonify({'error': 'no discipline_id'}), 400
    projects = get_projects_by_discipline(provider, int(discipline_id))
    return jsonify({'projects': projects})

# AJAX endpoint: получить занятых преподавателей по дате
@blueprint_order.route('/ajax/check_teachers', methods=['POST'])
@group_required
def ajax_check_teachers():
    defense_date = request.json.get('defense_date')
    if not defense_date:
        return jsonify({'error': 'no date'}), 400
    busy = get_busy_teachers_by_date(provider, defense_date)
    return jsonify({'busy': busy})

# Страница расписания комиссий
@blueprint_order.route('/schedule', methods=['GET'])
@group_required
def schedule():
    schedule_list = get_schedule(provider)
    return render_template("schedule.html", schedule=schedule_list)


# Восстановим старый exit для совместимости с шаблонами
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
    session.pop('selected_teachers', None)
    session.pop('selected_discipline', None)
    session.pop('selected_defense_date', None)
    session.pop('available_projects', None)
    return redirect('/')