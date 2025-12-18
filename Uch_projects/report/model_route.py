from dataclasses import dataclass
from database.select import select_list, stored_proc

@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route_create(proc_name:str, user_input: dict):
    rep_type = report_dict[rep_id]['type']

    if rep_type == 'by_date':
        user_list = [
            rep_type,
            int(user_input['month']),
            int(user_input['year']),
            None
        ]
    elif rep_type == 'by_teacher':
        user_list = [
            rep_type,
            None,
            None,
            int(user_input['teacher_id'])
        ]

    print(user_list, proc_name)

    message = stored_proc(proc_name, user_list)
    if message == '':
        return False
    return message

def model_route_show(provider, user_input: dict, sql_file: str):
    err_message = ""
    rep_type = report_dict[rep_id]['type']

    if rep_type == 'by_date':
        user_list = [
            rep_type,
            int(user_input['month']),
            int(user_input['year']),
            None
        ]
    elif rep_type == 'by_teacher':
        user_list = [
            rep_type,
            None,
            None,
            int(user_input['teacher_id'])
        ]

    _sql = provider.get(sql_file)
    print("sql=",_sql)
    result, schema = select_list(_sql, user_list)
    print("result=", result)
    print("schema=", schema)
    if result:
        return ResultInfo(result=result, status=True, err_message=err_message), schema
    else:
        return ResultInfo(result=result, status=False, err_message="DATA NOT FOUND"), schema