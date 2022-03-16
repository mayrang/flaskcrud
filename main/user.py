from main import *
from flask import Blueprint

bp = Blueprint("user", __name__, url_prefix="/user")

@bp.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        password1 = request.form.get("password1", type=str)
        password2 = request.form.get("password2", type=str)
        if name == "" or email == "" or password1 == "" or password2 == "":
            flash("입력하지 않은 항목이 있습니다.")
            return redirect(url_for("user.member_join"))
        if password1 != password2:
            flash("비밀번호가 일치하지 않습니다")
            return redirect(url_for("user.member_join"))
        user = mongo.db.user
        cnt = user.count_documents({"email": email})
        print(cnt)
        if cnt > 0:
            flash("중복되는 이메일이 있습니다.")
            return redirect(url_for("user.member_join"))
        created_utc_time = round(datetime.utcnow().timestamp() * 1000)
        query = {
            "name": name,
            "email": email,
            "password": hash_password(password1),
            "created_utc_time": created_utc_time,
            "logintime": "",
            "logincount": 0,
        }
        user.insert_one(query)
        return redirect(url_for("board.lists"))
    else:
        return render_template("join.html")


@bp.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email", type=str)
        password = request.form.get("password", type=str)
        next_url = request.form.get("next_url", type=str)
        if email is None or password is None:
            flash("입력하세요!")
            return redirect(url_for("user.login"))
        user = mongo.db.user
        data = user.find_one({"email": email})
        if data is None:
            flash("이메일 정보가 없습니다.")
            return redirect(url_for("user.login"))
        else:
            if check_password(data.get("password"), password):
                session["id"] = str(data.get("_id"))
                session["email"] = email
                session["name"] = data.get("name")
                session.permanent = True
                if next_url is not None:
                    return redirect(next_url)
                else:
                    return redirect(url_for("board.lists"))
            else:
                flash("비밀번호가 올바르지 않습니다.")
                return redirect(url_for("user.login"))
    else:
        return render_template("login.html")
    

@bp.route("/logout")
def logout():
    del session["id"]
    del session["name"]
    del session["email"]
    return redirect(url_for("board.lists"))