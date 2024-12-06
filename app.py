from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
import pytz
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 사용된 코드 저장
used_codes = set()

@app.route('/healthcheck')
def healthcheck():
    return "App is alive!", 200

def validate_code(code):
    """코드 검증 함수"""
    return len(code) == 8 and code[0] == '4' and code[2] == '9' and code[4] == '3' and code[6] == '6'

@app.route("/", methods=["GET", "POST"])
def code_input():
    """8자리 코드 입력 화면"""
    if 'validated' in session:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        code = request.form.get("code")
        if validate_code(code) and code not in used_codes:
            session['validated'] = True
            used_codes.add(code)
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie("validated", "true", max_age=60*60*24*30)  # 30일간 쿠키 유지
            return resp
        else:
            return render_template("code_input.html", error="Invalid or used code.")
    return render_template("code_input.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    """메인 페이지"""
    if 'validated' not in session:
        return redirect(url_for('code_input'))

    if request.method == "POST":
        # 할 일 처리
        pass
    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """관리자 페이지"""
    global used_codes
    if request.method == "POST":
        code_to_delete = request.form.get("code")
        if code_to_delete in used_codes:
            used_codes.remove(code_to_delete)
    return render_template("admin.html", used_codes=list(used_codes))

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=false)
