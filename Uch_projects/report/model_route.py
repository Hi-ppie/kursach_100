from dataclasses import dataclass
from database.select import select_list, stored_proc


@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route_create(proc_name: str, rep_type: str, user_input: dict):

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
    else:
        return False

    msg = stored_proc(proc_name, user_list)  # ← Получаем msg

    if msg:
        result_message = msg[0][0]  # ← ИСПРАВЛЕНИЕ: [0][0] вместо [0]['result'], т.к. это tuple с одной строкой
        if 'успешно создан' in result_message:
            return True
        else:
            return False  # Включая 'уже существует'
    else:
        return False  # Если msg пустой или ошибка



def model_route_show(provider, rep_type: str, user_input: dict, sql_file: str):
    """
    Отображение отчёта
    """

    if rep_type == 'by_date':
        sql_params = [
            int(user_input['month']),
            int(user_input['year'])
        ]

    elif rep_type == 'by_teacher':
        sql_params = [
            int(user_input['teacher_id'])
        ]
    else:
        return ResultInfo(result=(), status=False, err_message="UNKNOWN REPORT TYPE"), ()

    _sql = provider.get(sql_file)
    result, schema = select_list(_sql, sql_params)

    if result:
        return ResultInfo(result=result, status=True, err_message=""), schema
    else:
        return ResultInfo(result=result, status=False, err_message="DATA NOT FOUND"), schema
