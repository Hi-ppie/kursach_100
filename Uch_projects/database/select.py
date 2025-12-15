from database.DBcm import DBContextManager
from flask import current_app, session

def select_list(_sql: str, user_list: list):
    result = None
    schema = []
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Курсор не создан')
        else:
            cursor.execute(_sql, user_list)
            result = cursor.fetchall()
            for item in cursor.description:
                schema.append(item[0])
    return result, schema

def select_dict(_sql, user_dict: dict):
    user_list = list(user_dict.values())
    result, schema = select_list(_sql, user_list)
    result_dict = []
    for item in result:
        result_dict.append(dict(zip(schema, item)))
    print(result_dict)
    return result_dict

def stored_proc(proc_name: str, rep_date: list):
    msg=''
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Курсор не создан')
        else:
            cursor.callproc(proc_name, rep_date)
            msg = cursor.fetchall()
    return msg

def insert_many(_sql1: str, _sql2: str):
    last_inserted = None  # Инициализируем перед try
    try:
        with DBContextManager(current_app.config['db_config']) as cursor:
            if cursor is None:
                raise ValueError('Курсор не создан')
            else:
                user_dict = {'defense_date': session.get('defense_date'), 'project_id': session.get('project_id')}
                cursor.execute(_sql1, user_dict)
                if cursor.rowcount == 0:
                    raise ValueError('Insert не выполнен')
                last_inserted = cursor.lastrowid
                print("INSERT")
                for item in session['basket']:
                    session['basket'][item]['o_id'] = last_inserted
                    session['basket'][item]['teacher_id'] = int(item)
                    cursor.execute(_sql2, session['basket'][item])
                    print("INSERT")
        return last_inserted
    except Exception as e:
        print(e)
        return False

def insert(_sql: str, user_dict: dict):
    last_inserted = None  # Инициализируем перед try
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Курсор не создан')
        else:
            cursor.execute(_sql, user_dict)
            last_inserted = cursor.lastrowid  # Для DELETE = 0
    return last_inserted

def execute_sql(_sql: str, user_dict: dict):
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Курсор не создан')
        cursor.execute(_sql, user_dict)
        if cursor.rowcount == 0:
            print("WARNING: SQL executed but no rows affected")
    return True
