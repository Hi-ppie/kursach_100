from database.DBcm import DBContextManager
from flask import current_app, session

def select_list(_sql: str, user_list: list):
    result = []
    schema = []
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Курсор не создан')
        else:
            # Подготовка параметров: повторяем user_list столько раз,
            # сколько требуется для заполнения всех плейсхолдеров %s в SQL.
            placeholders = _sql.count('%s')
            if len(user_list) == 0:
                full_params = []
            else:
                multiplier = placeholders // len(user_list) if placeholders >= len(user_list) else 1
                full_params = user_list * multiplier

            cursor.execute(_sql, full_params)
            result.append(cursor.fetchall())
            if cursor.description:
                schema.append([item[0] for item in cursor.description])
            while cursor.nextset():
                result.append(cursor.fetchall())
                if cursor.description:
                    schema.append([item[0] for item in cursor.description])
    return result, schema

def select_dict(_sql, user_dict: dict):
    user_list = list(user_dict.values())
    results, schemas = select_list(_sql, user_list)

    result_dict = []
    # Преобразуем только первый result-set в список словарей (как ожидает остальной код)
    if results and schemas:
        first_rows = results[0]
        first_schema = schemas[0] if schemas else []
        for row in first_rows:
            result_dict.append(dict(zip(first_schema, row)))

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