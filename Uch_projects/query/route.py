import os
import json
import datetime
import re
from collections import OrderedDict
from flask import Blueprint, render_template, request
from access import group_required
from query.model_route import model_route
from database.sql_provider import SQLProvider

blueprint_query = Blueprint(
    'blueprint_query',
    __name__,
    template_folder='templates'
)

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

with open("data/query.json", encoding="utf-8") as f:
    query_dict = json.load(f)


def try_parse_date(date_str: str):
    if not date_str:
        return None
    s = date_str.strip()
    formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%m.%d.%Y']
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(s, fmt).date()
            return dt.isoformat()
        except Exception:
            continue
    m = re.search(r'(\d{1,2})\D+(\d{1,2})\D+(\d{2,4})', s)
    if m:
        d, mth, y = m.group(1), m.group(2), m.group(3)
        try:
            y_full = y if len(y) == 4 else ('20' + y)
            dt = datetime.date(int(y_full), int(mth), int(d))
            return dt.isoformat()
        except Exception:
            try:
                dt2 = datetime.date(int(y_full), int(d), int(mth))
                return dt2.isoformat()
            except Exception:
                return None
    return None


@blueprint_query.route('/', methods=["GET"])
@group_required
def query_menu():
    return render_template("query_menu.html")


@blueprint_query.route('/query', methods=["GET"])
@group_required
def query_index():
    query_id = request.args.get('id')
    if not query_id or query_id not in query_dict:
        return render_template("err.html", id=None)
    return render_template(query_dict[query_id]['input'])


@blueprint_query.route('/result', methods=["POST"])
@group_required
def query_result():
    query_id = request.args.get('id')
    if not query_id or query_id not in query_dict:
        return render_template("err.html", id=None)

    sql_file = query_dict[query_id]['file_name']
    params = OrderedDict()

    try:
        if query_id == '1':
            raw = request.form.get('defense_date', '').strip()
            parsed = try_parse_date(raw)
            if not parsed:
                return render_template("err.html", id=query_id)
            params['defense_date'] = parsed

        elif query_id == '2':
            val = request.form.get('surname', '').strip()
            if not val:
                return render_template("err.html", id=query_id)
            params['surname'] = val

        elif query_id == '3':
            val = request.form.get('surname', '').strip()
            if not val:
                return render_template("err.html", id=query_id)
            params['surname'] = val

        elif query_id == '4':
            raw = request.form.get('topic', '').strip()
            if not raw:
                return render_template("err.html", id=query_id)

            # ищем trailing number (Project1 или "Project 1")
            m_end = re.search(r'(\d+)\s*$', raw)
            if m_end:
                pid = int(m_end.group(1))
            else:
                # если нет в конце, ищем любой числовой токен
                m_any = re.search(r'(\d+)', raw)
                pid = int(m_any.group(1)) if m_any else -1

            # Подготавливаем параметры В ТОЧНОМ порядке, который ожидает lib4.sql:
            # SQL ожидает: %s (pid), %s (pid), %s (topic_exact), %s (pid), %s (pattern)
            params['pid_a'] = pid                 # %s 1
            params['pid_b'] = pid                 # %s 2
            params['topic_exact'] = raw           # %s 3
            params['pid_c'] = pid                 # %s 4
            params['pattern'] = f"%{raw}%"        # %s 5

            # Убедимся, что используем lib4.sql
            sql_file = 'lib4.sql'

        else:
            return render_template("err.html", id=query_id)

    except Exception as e:
        print("query_result param prepare error:", e)
        return render_template("err.html", id=query_id)

    result_info = model_route(provider, params, sql_file)

    if result_info.status:
        return render_template(
            query_dict[query_id]['output'],
            results=result_info.result,
            id=query_id
        )
    else:
        return render_template("err.html", id=query_id)