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