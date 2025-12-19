import os
import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from order.model_route import (
    model_route, model_route_add, model_route_insert, model_route_delete, load_basket_from_db,
    get_disciplines, get_projects_by_discipline, create_commissions, get_busy_teachers_by_date, get_schedule
)
from database.sql_provider import SQLProvider
from database.select import execute_sql
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
        teacher_ids = request.form.getlist('teacher_id')
        project_ids = request.form.getlist('project_id')
        defense_date = request.form.get('defense_date')
        if not teacher_ids or not project_ids or not defense_date:
            return render_template("basket_err.html", error="не выбраны преподаватели/проекты/дата")
        all_projects = []
        discipline_id = request.form.get('discipline_id')
        if discipline_id:
            projects_all = get_projects_by_discipline(provider, int(discipline_id))
            for p in projects_all:
                if str(p['project_id']) in project_ids:
                    all_projects.append(p)
        created, skipped = create_commissions(provider, [int(x) for x in teacher_ids], all_projects, defense_date)
        return render_template("commission_result.html", created=created, skipped=skipped)


# AJAX endpoint: получить проекты по дисциплине (JSON)
@blueprint_order.route('/ajax/projects', methods=['POST'])
@group_required
def ajax_projects():
    discipline_id = None
    try:
        if request.is_json:
            discipline_id = request.json.get('discipline_id')
        else:
            discipline_id = request.form.get('discipline_id')
    except Exception:
        pass
    if not discipline_id:
        return jsonify({'error': 'no discipline_id'}), 400
    projects = get_projects_by_discipline(provider, int(discipline_id))
    # Конвертируем даты в строки, чтобы jsonify не сломался в браузере
    for p in projects:
        for k, v in list(p.items()):
            if isinstance(v, (datetime.date, datetime.datetime)):
                p[k] = v.isoformat()
    return jsonify({'projects': projects})


# AJAX endpoint: получить занятых преподавателей по дате
@blueprint_order.route('/ajax/check_teachers', methods=['POST'])
@group_required
def ajax_check_teachers():
    defense_date = None
    try:
        if request.is_json:
            defense_date = request.json.get('defense_date')
        else:
            defense_date = request.form.get('defense_date')
    except Exception:
        pass
    if not defense_date:
        return jsonify({'error': 'no date'}), 400
    busy = get_busy_teachers_by_date(provider, defense_date)
    return jsonify({'busy': busy})


# AJAX endpoint: удалить комиссию по cs_id (удаляет сначала членов, затем сам график)
@blueprint_order.route('/ajax/delete_cs', methods=['POST'])
@group_required
def ajax_delete_cs():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        cs_id = data.get('cs_id')
        if not cs_id:
            return jsonify({'ok': False, 'error': 'no cs_id provided'}), 400
        # Удаляем членов комиссии, затем сам график (сначала members, иначе FK)
        sql_del_members = "DELETE FROM commission_members WHERE cs_id = %(cs_id)s;"
        sql_del_schedule = "DELETE FROM commission_schedule WHERE cs_id = %(cs_id)s;"
        execute_sql(sql_del_members, {'cs_id': cs_id})
        execute_sql(sql_del_schedule, {'cs_id': cs_id})
        return jsonify({'ok': True})
    except Exception as e:
        print("ajax_delete_cs error:", e)
        return jsonify({'ok': False, 'error': str(e)}), 500


# Страница расписания комиссий (FullCalendar)
@blueprint_order.route('/schedule', methods=['GET'])
@group_required
def schedule():
    schedule_list = get_schedule(provider)
    # Конвертируем даты в ISO-строки (чтобы template.tojson корректно сериализовал)
    for row in schedule_list:
        v = row.get('cs_date')
        if isinstance(v, (datetime.date, datetime.datetime)):
            row['cs_date'] = v.isoformat()
        if row.get('project_topic') is None:
            row['project_topic'] = ''
    return render_template("schedule.html", schedule=schedule_list)


# debug endpoint — вернуть готовые события для FullCalendar (используется сайтом schedule)
@blueprint_order.route('/debug_events', methods=['GET'])
@group_required
def debug_events():
    try:
        schedule_list = get_schedule(provider)

        # Получим всех преподавателей (teacher_id -> surname)
        teachers_info = model_route(provider, {}, 'teachers.sql')
        teacher_map = {}
        if teachers_info.status:
            for t in teachers_info.result:
                teacher_map[int(t['teacher_id'])] = t.get('surname', str(t.get('teacher_id')))

        # Нормализуем даты и project_topic
        for row in schedule_list:
            v = row.get('cs_date')
            if isinstance(v, (datetime.date, datetime.datetime)):
                row['cs_date'] = v.isoformat()
            if row.get('project_topic') is None:
                row['project_topic'] = ''

        # Группируем по cs_id и формируем events (title: "Project (Surname1, Surname2)")
        grouped = {}
        for r in schedule_list:
            cid = r['cs_id']
            if cid not in grouped:
                grouped[cid] = {
                    'cs_id': cid,
                    'cs_date': r['cs_date'],
                    'project': r['project_topic'] or ('Проект ' + str(r.get('project_id'))),
                    'teachers': []
                }
            if r.get('teacher_id'):
                grouped[cid]['teachers'].append(int(r['teacher_id']))

        events = []
        for g in grouped.values():
            # заменяем id на фамилии (если есть), иначе оставляем id
            surnames = [teacher_map.get(tid, str(tid)) for tid in g['teachers']]
            title = g['project']
            if surnames:
                title = f"{title} ({', '.join(surnames)})"
            events.append({'id': g['cs_id'], 'title': title, 'start': g['cs_date']})

        return jsonify(events)
    except Exception as e:
        print("DEBUG_EVENTS error:", e)
        return jsonify({'error': str(e)}), 500


# Alias для совместимости со старыми шаблонами — перенаправляет на одностраничный поток
@blueprint_order.route('/', methods=["GET"])
@group_required
def order_index():
    return redirect(url_for('blueprint_order.create'))


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