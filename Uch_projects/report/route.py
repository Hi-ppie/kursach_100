import os
import json
from flask import Blueprint, render_template, request, redirect, url_for
from access import group_required
from report.model_route import model_route_create, model_route_show
from database.sql_provider import SQLProvider

blueprint_report = Blueprint(
    'blueprint_report',
    __name__,
    template_folder='templates'
)

# SQL-файлы отчётов
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

# report.json лежит в Uch_projects/data/, а не в report/data/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
with open(os.path.join(BASE_DIR, 'data', 'report.json'), encoding='utf-8') as f:
    report_dict = json.load(f)


@blueprint_report.route('/', methods=["GET"])
@group_required
def report_menu():
    # items = список (название, id) для меню
    rep = [(item["name"], item["id"]) for item in report_dict.values()]
    return render_template("report_menu.html", items=rep)


@blueprint_report.route('/report', methods=["GET"])
@group_required
def report_index():
    rep_id = request.args.get('id')
    if not rep_id or rep_id not in report_dict:
        return render_template('report_err.html', id='', message='Неизвестный отчёт.')
    return render_template('report_index.html', item=report_dict[rep_id])


@blueprint_report.route('/result', methods=["POST"])
@group_required
def report_result():
    user_input = request.form
    rep_id = request.args.get('id') or user_input.get('id')

    if not rep_id or rep_id not in report_dict:
        return redirect(url_for('blueprint_report.report_menu'))

    rep_cfg = report_dict[rep_id]

    # === СОЗДАНИЕ ОТЧЁТА ===
    if user_input.get('action') == 'Создать':
        result_info = model_route_create(
            rep_cfg['proc'],
            rep_cfg['type'],  # by_date / by_teacher
            user_input
        )
        return render_template(
            "report_create.html",
            item=(result_info or ''),
            user=user_input,
            id=rep_id
        )

    # === ПРОСМОТР ОТЧЁТА ===
    else:
        results, schema, stat = model_route_show(
            provider,
            rep_cfg['type'],
            user_input,
            rep_cfg['sql']
        )

        if results.status:
            return render_template(
                "report_show.html",
                schema=schema,
                results=results.result,
                item=rep_cfg,
                date=user_input,
                id=rep_id,
                stat=stat
            )
        else:
            # Тут делаем разный текст для разных типов отчётов
            if rep_cfg['type'] == 'by_teacher':
                msg = (
                    'Отчёт по этому преподавателю ещё не создан или данных нет. '
                    'Сначала нажмите "Создать", затем "Посмотреть".'
                )
            else:
                msg = 'Отчёт за указанный период не найден!'

            return render_template(
                "report_err.html",
                id=rep_id,
                message=msg
            )