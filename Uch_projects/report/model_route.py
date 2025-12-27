from dataclasses import dataclass
from database.select import select_list, stored_proc

@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route_create(proc_name: str, rep_type: str, user_input: dict):
    if rep_type == 'by_date':
        params = ['by_date', int(user_input.get('month')), int(user_input.get('year')), None]
    elif rep_type == 'by_teacher':
        params = ['by_teacher', None, None, int(user_input.get('teacher_id'))]
    else:
        return ''  # важно вернуть строку, чтобы не попасть в fallback

    msg = stored_proc(proc_name, params)
    return msg or 'Процедура не вернула статус'


def model_route_show(provider, rep_type: str, user_input: dict, sql_file: str):
    """
    Отображение отчёта

    Возвращает: (ResultInfo, schema_columns, stat_rows_or_None)
    """

    # Подготовка параметров в зависимости от типа отчёта
    try:
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
            print(f"[model_route_show] Unknown report type: {rep_type}")
            return ResultInfo(result=(), status=False, err_message="UNKNOWN REPORT TYPE"), (), None
    except KeyError as e:
        print(f"[model_route_show] Missing parameter: {e} - input: {user_input}")
        return ResultInfo(result=(), status=False, err_message="MISSING PARAM"), (), None
    except ValueError as e:
        print(f"[model_route_show] Invalid parameter value: {e} - input: {user_input}")
        return ResultInfo(result=(), status=False, err_message="INVALID PARAM"), (), None

    # Получаем SQL и выполняем
    _sql = provider.get(sql_file)
    print(f"[model_route_show] Executing SQL file: {sql_file}")
    print(f"[model_route_show] SQL (first 200 chars): {_sql[:200]!r}")
    print(f"[model_route_show] Params: {sql_params}")

    try:
        results, schemas = select_list(_sql, sql_params)
    except Exception as e:
        print(f"[model_route_show] DB error during select_list: {e}")
        return ResultInfo(result=(), status=False, err_message="DB ERROR"), (), None

    # Отладочная информация о результатах
    try:
        print(f"[model_route_show] Number of result sets: {len(results)}")
        for i, rset in enumerate(results):
            print(f"[model_route_show] Result set {i}: rows={len(rset)}")
        print(f"[model_route_show] Schemas: {schemas}")
    except Exception as e:
        print(f"[model_route_show] Error while introspecting results: {e}")

    # Основной результат — первый result-set
    if results and results[0]:
        # schemas[0] — список имён колонок для первого result-set, results[1] — второе result-set (stat) если есть
        return ResultInfo(result=results[0], status=True, err_message=""), (schemas[0] if schemas else ()), (results[1] if len(results) > 1 else None)
    else:
        print(f"[model_route_show] No data found for params: {sql_params}")
        return ResultInfo(result=(), status=False, err_message="DATA NOT FOUND"), (), None