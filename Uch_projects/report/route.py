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

# 🔧 ВАЖНО: report.json лежит в Uch_projects/data/, а не в report/data/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
with open(os.path.join(BASE_DIR, 'data', 'report.json'), encoding='utf-8') as f:
    report_dict = json.load(f)


@blueprint_report.route('/', methods=["GET"])
@group_required
def report_menu():
    rep = [(item["name"], item["id"]) for item in report_dict.values()]
    return render_template("report_menu.html", items=rep)


@blueprint_report.route('/report', methods=["GET"])
@group_required
def report_index():
    rep_id = request.args.get('id')
    return render_template('report_index.html', item=report_dict[rep_id])


@blueprint_report.route('/result', methods=["POST"])
@group_required
def report_result():
    user_input = request.form
    rep_id = request.args.get('id') or user_input.get('id')

    if not rep_id:
        return redirect(url_for('blueprint_report.report_menu'))

    if user_input.get('action') == 'Создать':
        result_info = model_route_create(
            report_dict[rep_id]['proc'],
            report_dict[rep_id]['type'],  # ← ВАЖНО
            user_input
        )

        if result_info:
            return render_template(
                "report_create.html",
                item=result_info,
                user=user_input,
                id=rep_id
            )
        else:
            return render_template(
                "report_err.html",
                id=rep_id,
                message='Отчёт уже существует или не может быть создан! Нажмите "Посмотреть" для просмотра.'
            )


    else:
        results, schema, stat = model_route_show(
            provider,
            report_dict[rep_id]['type'],
            user_input,
            report_dict[rep_id]['sql']
        )
        if results.status:
            return render_template(
                "report_show.html",
                schema=schema,
                results=results.result,
                item=report_dict[rep_id],
                date=user_input,
                id=rep_id,
                stat=stat  # Добавьте это
            )
        else:
            return render_template(
                "report_err.html",
                id=rep_id,
                message='Отчёт за указанный период не найден!'
            )