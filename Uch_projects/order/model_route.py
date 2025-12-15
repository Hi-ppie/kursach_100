from dataclasses import dataclass
from database.select import select_dict, insert_many, execute_sql
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

def load_basket_from_db(provider, project_id):
    _sql = provider.get('load_commission.sql')
    result = select_dict(_sql, {'project_id': project_id})

    session['basket'] = {}
    for res in result:
        id_str = str(res['teacher_id'])
        session['basket'][id_str] = {
            'teacher_surname': res['surname'],
            'teacher_account': res['account_num'],
            'teacher_number': 1
        }
