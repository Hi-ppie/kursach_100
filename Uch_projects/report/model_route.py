from dataclasses import dataclass
from database.select import select_list, stored_proc

@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route_create(proc_name:str, user_input: dict):
    user_list = [int(user_input['month']),int(user_input['year'])]
    print(user_list, proc_name)

    message = stored_proc(proc_name, user_list)
    if message == '':
        return False
    return message

def model_route_show(provider, user_input: dict, sql_file: str):
    err_message = ""
    user_list = [int(user_input['month']), int(user_input['year'])]
    _sql = provider.get(sql_file)
    print("sql=",_sql)
    result, schema = select_list(_sql, user_list)
    print("result=", result)
    print("schema=", schema)
    if result:
        return ResultInfo(result=result, status=True, err_message=err_message), schema
    else:
        return ResultInfo(result=result, status=False, err_message="DATA NOT FOUND"), schema