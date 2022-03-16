from main import *
from flask import Blueprint, jsonify, send_from_directory
from main.common import allowed_file, random_generator


bp = Blueprint("board", __name__, url_prefix="/board") 


def board_delete_attach_file(filename):
    abs_path = os.path.join(app.config["BOARD_ATTACH_FILE_PATH"], filename)
    if os.path.exists(abs_path):
        os.remove(abs_path)
        return True
    return False

@bp.route("/lists")
def lists():
    page = request.args.get("page", 1, int)
    limit = 10
    search_list = []
    query = {}
    search = request.args.get("search", -1, int)
    keyword = request.args.get("keyword", "",  str)
    if search == 0:
        search_list.append({"title": {"$regex": keyword}})
    elif search == 1:
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 2:
        search_list.append({"title": {"$regex": keyword}})
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 3:
        search_list.append({"name": {"$regex": keyword}})
    if len(search_list) > 0:
        query = {"$or": search_list}
    board = mongo.db.board
    datas = board.find(query).skip(limit * (page-1)).limit(limit)
    total_count = board.count_documents(query)
    last_page_num = math.ceil(total_count/limit)
    block_size = 5
    page_block = int((page-1) / block_size)
    block_start = page_block * block_size + 1
    block_last = block_start + block_size - 1
    return render_template("lists.html",
                           datas=datas,
                           page=page,
                           limit=limit,
                           search=search,
                           keyword=keyword,
                           last_page_num=last_page_num,
                           page_block=page_block,
                           block_start=block_start,
                           block_last=block_last)


@bp.route("/view/<idx>")
def board_view(idx):
    if idx is not None:
        search = request.args.get("search", -1, type=int)
        keyword = request.args.get("keyword", type=str)
        board = mongo.db.board
        data = board.find_one_and_update({"_id": ObjectId(idx)},
                                         {"$inc": {"view_count": 1}},
                                         return_document=True)
        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "current_utc_time": data.get("current_utc_time"),
                "view_count": data.get("view_count"),
                "attachfile": data.get("attachfile", "")
            }
            return render_template("view.html",
                                   result=result,
                                   search=search,
                                   keyword=keyword,
                                   )
    return abort(400)


@bp.route("/write", methods=["POST", "GET"])
@login_required
def board_write():
    if request.method == "POST":
        filename = None
        if "attachfile" in request.files:
            file = request.files["attachfile"]
            if file and allowed_file(file.filename):
                filename = check_filename(file.filename)
                file.save(os.path.join(app.config["BOARD_ATTACH_FILE_PATH"], filename))
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")
        view_count = 0
        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.board
        post = {
            "name": name,
            "title": title,
            "contents": contents,
            "view_count": view_count,
            "current_utc_time": current_utc_time,
            "writer_id": session["id"]
        }
        if filename is not None:
            post["attachfile"] = filename
        x = board.insert_one(post)
        return redirect(url_for("board.board_view", idx=str(x.inserted_id)))
    else:
        return render_template("write.html")


@bp.route("/edit/<idx>", methods=["POST", "GET"])
@login_required
def edit(idx):
    if request.method == "GET":
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("board.lists"))
        else:
            if session.get("id") == data.get("writer_id"):
                return render_template("edit.html", data=data)
            else:
                flash("수정권한이 없습니다.")
                return redirect(url_for("board.board_view", idx=idx))
    else:
        title = request.form.get("title")
        contents = request.form.get("contents")
        deleteoldfile = request.form.get("deleteoldfile")
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})
        if session.get("id") == data.get("writer_id"):
            filename = None
            if "attachfile" in request.files:
                file = request.files["attachfile"]
                if file and allowed_file(file.filename):
                    filename = check_filename(file.filename)
                    file.save(os.path.join(app.config["BOARD_ATTACH_FILE_PATH"], filename))
                if data.get("attachfile"):
                    board_delete_attach_file(data.get("attachfile"))
            else:
                if deleteoldfile == "on":
                    board_delete_attach_file(data.get("attachflie"))
                else:
                    filename = data.get("attachfile")
                    
            board.update_one({"_id": ObjectId(idx)},
                             {"$set":
                                 {
                                    "title": title,
                                    "contents": contents,
                                    "attachfile": filename
                                  }})
            flash("수정되었습니다.")
            return redirect(url_for("board.board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("board.lists"))


@bp.route("/delete/<idx>")
@login_required
def delete(idx):
    board = mongo.db.board
    data = board.find_one({"_id": ObjectId(idx)})
    if session.get("id") == data.get("writer_id"):
        board.delete_one({"_id": ObjectId(idx)})
        return redirect(url_for("board.lists"))
    else:
        flash("삭제 권한이 없습니다.")
        return redirect(url_for("board.board_view", idx=idx))
    

@bp.route("/upload_image", methods=["POST"])
def upload_image():
    if request.method == "POST":
        file = request.files["image"]
        if file and allowed_file(file.filename):
            filename = "{}.{}".format(random_generator(), get_extension(file.filename))
            savefilepath = os.path.join(app.config["BOARD_IMAGE_PATH"], filename)
            file.save(savefilepath)
            return url_for("board.image", filename=filename)
        

@bp.route("/image/<filename>")
def image(filename):
    return send_from_directory(app.config["BOARD_IMAGE_PATH"], filename)

@bp.route("/upload/<filename>")
def files(filename):
    return send_from_directory(app.config["BOARD_ATTACH_FILE_PATH"], filename, as_attachment=True)


@bp.route("/comment_list/<root_idx>", methods=["GET"])
def comment_list(root_idx):
    comment = mongo.db.comment
    comments = comment.find({"root_idx": str(root_idx)}).sort("current_utc_time", -1)
    comment_list = []
    for comment_value in comments:
        if comment_value.get("writer_id") == session.get("id"):
            owner = True
        else:
            owner = False
        comment_list.append({
            "error": "sucess",
            "id": str(comment_value.get("_id")),
            "root_idx": comment_value.get("root_idx"),
            "name" : comment_value.get("name"),
            "writer_id": comment_value.get("writer_id"),
            "comment": comment_value.get("comment"),
            "current_utc_time": format_datetime(comment_value.get("current_utc_time")),
            "owner": owner
        })
    return jsonify(error="success", lists=comment_list)

@bp.route("/comment_write", methods=["POST"])
@login_required
def comment_write():
    if request.method == "POST":
        c = mongo.db.comment
        root_idx = request.form.get("root_idx")

        comment = {
            "name": session.get("name"),
            "root_idx": root_idx,
            "comment": request.form.get("comment"),
            "current_utc_time": round(datetime.utcnow().timestamp() * 1000),
            "writer_id": session.get("id"),
        }

        c.insert_one(comment)
        return jsonify(error="success")
    else:
        abort(403)

@bp.route("/comment_delete", methods=["POST"])
@login_required
def comment_delete():
    idx = request.form.get("id")
    c = mongo.db.comment
    data = c.find_one({"_id": ObjectId(idx)})
    if data.get("writer_id") == session.get("id"):
        c.delete_one({"_id": ObjectId(idx)})
        return jsonify(error="success")
    else:
        return jsonify(error="error")
    

@bp.route("/comment_edit", methods=["POST"])
@login_required
def comment_edit():
    c = mongo.db.comment
    idx = request.form.get("id")
    comment = request.form.get("comment")
    data = c.find_one({"_id": ObjectId(idx)})
    if data.get("writer_id") == session.get("id"):
        c.update_one({"_id": ObjectId(idx)}, {"$set": {"comment": comment}})
        return jsonify(error="success")
    else:
        return jsonify(error="error")