from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_babel import Babel, _
from flask_session import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
import csv
import io
import os

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ko']
Session(app)
babel = Babel(app)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# User Data Storage
user_data = {}

# Multilingual support
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

# Routes
@app.route('/')
def index():
    user_id = session.get('user_id', request.remote_addr)
    session['user_id'] = user_id
    if user_id not in user_data:
        user_data[user_id] = {"name": None, "to_do_list": []}
    user_info = user_data[user_id]
    return render_template("index.html", user_name=user_info["name"], to_do_list=user_info["to_do_list"])

@app.route('/add_task', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if user_id not in user_data:
        return jsonify({"error": _("User not found")}), 400

    user_info = user_data[user_id]
    task = request.json.get('task')
    reminder_time = request.json.get('reminder_time')

    if task:
        task_entry = {"task": task, "reminder_time": reminder_time}
        user_info["to_do_list"].append(task_entry)
        if reminder_time:
            schedule_reminder(user_id, task, reminder_time)
    return jsonify(user_info["to_do_list"])

@app.route('/export_csv')
def export_csv():
    user_id = session.get('user_id')
    if not user_id or user_id not in user_data:
        return jsonify({"error": _("User not found")}), 400

    user_info = user_data[user_id]
    tasks = user_info["to_do_list"]

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["Task", "Reminder Time"])
    for task in tasks:
        writer.writerow([task["task"], task.get("reminder_time", "")])

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    si.close()

    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='todo_list.csv')

@app.route('/calendar')
def calendar():
    user_id = session.get('user_id')
    if not user_id or user_id not in user_data:
        return jsonify({"error": _("User not found")}), 400

    user_info = user_data[user_id]
    return jsonify(user_info["to_do_list"])

@app.route('/set_language/<lang>')
def set_language(lang):
    session['lang'] = lang
    return redirect(url_for('index'))

def schedule_reminder(user_id, task, reminder_time):
    reminder_time_dt = datetime.strptime(reminder_time, '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    delay = (reminder_time_dt - now).total_seconds()
    if delay > 0:
        scheduler.add_job(func=send_notification, trigger="date", args=[user_id, task], run_date=reminder_time_dt)

def send_notification(user_id, task):
    # Notification logic can be implemented here
    print(f"Reminder for user {user_id}: {task}")

@app.route('/healthcheck')
def healthcheck():
    return "App is alive!", 200

if __name__ == '__main__':
    app.run(debug=True)
