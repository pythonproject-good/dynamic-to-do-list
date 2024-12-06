from flask import Flask, render_template, jsonify, request, redirect, url_for, session, make_response
from datetime import datetime
import pytz
from flask_session import Session

app = Flask(__name__)

# Flask-Session 설정
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# 전역 데이터 저장
user_data = {}  # 사용자별 데이터 저장
used_codes = set()  # 사용된 코드 저장

@app.route('/healthcheck')
def healthcheck():
    return "App is alive!", 200

@app.route('/status')
def status():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET", "POST"])
def index():
    # 세션 및 인증 확인
    user_id = session.get('user_id')
    if not user_id or not request.cookies.get('auth_passed'):
        return redirect(url_for("auth"))
    
    # 사용자 데이터 초기화
    if user_id not in user_data:
        user_data[user_id] = {"name": None, "to_do_list": []}
    user_info = user_data[user_id]
    
    if request.method == "POST":
        if "name" in request.form:
            user_info["name"] = request.form["name"]
        if "task" in request.form:
            task = request.form["task"]
            if task:
                user_info["to_do_list"].append(task)
        return redirect(url_for("index"))

    return render_template("index.html", user_name=user_info["name"], to_do_list=user_info["to_do_list"])

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        code = request.form.get("code")
        if code and len(code) == 8 and code[0] == "4" and code[2] == "9" and code[4] == "3" and code[6] == "6" and code not in used_codes:
            used_codes.add(code)
            session['user_id'] = request.remote_addr
            resp = make_response(redirect(url_for("index")))
            resp.set_cookie("auth_passed", "true", max_age=60 * 60 * 24)
            return resp
        return "Invalid code or code already used.", 403
    return render_template("code_input.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        code = request.form.get("delete_code")
        if code in used_codes:
            used_codes.remove(code)
    return render_template("admin.html", codes=list(used_codes))

@app.route("/time")
def get_time():
    kst = pytz.timezone('Asia/Seoul')
    current_time_kst = datetime.now(kst)
    return jsonify({
        "hours": current_time_kst.hour,
        "minutes": current_time_kst.minute,
        "seconds": current_time_kst.second
    })

@app.route("/todos", methods=["POST"])
def add_task():
    user_id = session.get('user_id')
    if not user_id or user_id not in user_data:
        return jsonify([])

    user_info = user_data[user_id]
    task = request.json.get("task")
    if task:
        user_info["to_do_list"].append(task)
    return jsonify(user_info["to_do_list"])

@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_task(index):
    user_id = session.get('user_id')
    if not user_id or user_id not in user_data:
        return jsonify([])

    user_info = user_data[user_id]
    if 0 <= index < len(user_info["to_do_list"]):
        user_info["to_do_list"].pop(index)
    return jsonify(user_info["to_do_list"])

if __name__ == "__main__":
    app.run(host="0.0.0.0")
