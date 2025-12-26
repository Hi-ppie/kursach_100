from dataclasses import dataclass
from database.select import select_dict, insert_many, execute_sql, insert, select_list
from flask import session

@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str

def model_route(provider, user_input: dict, sql_file: str):
    err_message = ""
    _sql = provider.get(sql_file)
    result = select_dict(_sql, user_input)
    if result:
        return ResultInfo(result=result, status=True, err_message=err_message)
    else:
        return ResultInfo(result=result, status=False, err_message="DATA NOT FOUND")


def model_route_add(provider, user_input: dict, sql_file: str):
    _sql = provider.get(sql_file)
    substr = False
    if 'action' in user_input and user_input['action'] == 'Удалить':
        substr = True
    user_dict = {'teacher_id': user_input['teacher_id']}
    result = select_dict(_sql, user_dict)
    if result:
        add_to_basket(result[0],substr)
        return True
    else:
        return False

def add_to_basket(teachers: dict,substr: bool):
    if 'basket' not in session:
        session['basket'] = {}
    teacher_id = str(teachers['teacher_id'])
    if substr:
        session['basket'].pop(teacher_id)
        return True
    else:
        session['basket'][teacher_id] = {'teacher_surname': teachers['surname'],'teacher_account': teachers['account_num'], 'teacher_number': 1}
    return True

def model_route_insert(provider, sql_file1: str, sql_file2: str, sql_check: str):
    if check_basket(provider,sql_check):
        return False
    _sql1 = provider.get(sql_file1)
    _sql2 = provider.get(sql_file2)
    result = insert_many(_sql1, _sql2)
    if result:
        cs_id = result
        return cs_id
    return False

def check_basket(provider, sql_file: str):
    _sql = provider.get(sql_file)
    result = select_dict(_sql, {})
    basket = session.get('basket')
    for item in result:
        for key in basket:
            if int(key) == item['teacher_id'] and basket[key]['teacher_number'] > item['teacher_number']:
                return True
    return False

def model_route_delete(provider, user_input: dict):

    _sql_members = provider.get('delete_commission_members.sql')
    _sql_schedule = provider.get('delete_commission_schedule.sql')

    execute_sql(_sql_members, user_input)
    execute_sql(_sql_schedule, user_input)

    return True


# -------------------------
# Новая логика для одностраничного создания комиссии (AJAX-friendly)
# -------------------------

def get_disciplines(provider):
    _sql = provider.get('get_disciplines.sql')
    return select_dict(_sql, {})

def get_projects_by_discipline(provider, discipline_id: int):
    # select_dict ожидает dict
    _sql = provider.get('projects_by_discipline.sql')
    return select_dict(_sql, {'discipline_id': discipline_id})

def get_busy_teachers_by_date(provider, defense_date: str):
    """
    Возвращает список teacher_id, у которых есть комиссия на указанную дату.
    """
    _sql = provider.get('get_busy_teachers.sql')
    # используем select_list, т.к. хочется получить «сырые» кортежи
    results, schemas = select_list(_sql, [defense_date])
    busy = []
    if results and results[0]:
        for row in results[0]:
            busy.append(row[0])
    return busy

def get_schedule(provider):
    """
    Возвращает расписание комиссий в сгруппированном виде:

    [
      {
        'cs_date': date,
        'commissions': [
          {
            'cs_id': ...,
            'project_id': ...,
            'project_topic': ...,
            'discipline_name': ...,
            'student_surname': ...,
            'supervisor_surname': ...,
            'teachers': [ 'Teacher1', 'Teacher2', ... ]
          },
          ...
        ]
      },
      ...
    ]
    """
    _sql = provider.get('get_schedule.sql')
    results, schemas = select_list(_sql, [])
    schedule = []

    if not (results and schemas and results[0]):
        return schedule

    cols = schemas[0]
    rows = [dict(zip(cols, row)) for row in results[0]]

    # Группируем: сначала по дате, внутри по cs_id
    grouped_by_date = {}

    for r in rows:
        cs_date = r['cs_date']
        cs_id = r['cs_id']

        if cs_date not in grouped_by_date:
            grouped_by_date[cs_date] = {}

        commissions = grouped_by_date[cs_date]

        if cs_id not in commissions:
            commissions[cs_id] = {
                'cs_id': cs_id,
                'project_id': r['project_id'],
                'project_topic': r.get('project_topic'),
                'discipline_name': r.get('discipline_name'),
                'student_surname': r.get('student_surname'),
                'supervisor_surname': r.get('supervisor_surname'),
                'teachers': []
            }

        # Добавляем преподавателя, если он есть (LEFT JOIN может вернуть NULL)
        if r.get('teacher_surname'):
            commissions[cs_id]['teachers'].append(r['teacher_surname'])

    # Преобразуем в список, отсортированный по дате и cs_id
    for cs_date, commissions in sorted(grouped_by_date.items(), key=lambda x: x[0]):
        comm_list = list(commissions.values())
        comm_list.sort(key=lambda c: c['cs_id'])
        schedule.append({
            'cs_date': cs_date,
            'commissions': comm_list
        })

    return schedule

def create_commissions(provider, teacher_ids: list, projects: list, defense_date: str):

    created = []
    skipped = []

    _sql_insert_o = provider.get('insert_o.sql')     # INSERT commission_schedule (cs_date, project_id)
    _sql_insert_ol = provider.get('insert_ol.sql')   # INSERT commission_members (cs_id, teacher_id)

    for proj in projects:
        try:
            params_o = {'defense_date': defense_date, 'project_id': proj['project_id']}
            cs_id = insert(_sql_insert_o, params_o)
            if not cs_id:
                continue
            for t in teacher_ids:
                if int(t) == int(proj.get('supervisor_id')):
                    skipped.append({'project_id': proj['project_id'], 'teacher_id': int(t)})
                    continue
                params_member = {'o_id': cs_id, 'teacher_id': int(t)}
                insert(_sql_insert_ol, params_member)
            created.append({'project_id': proj['project_id'], 'cs_id': cs_id})
        except Exception as e:
            print(f"[create_commissions] Error for project {proj}: {e}")
            continue

    return created, skipped