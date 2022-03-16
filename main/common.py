from functools import wraps
from main import  session, request, url_for, redirect, ALLOWED_EXTENSIONS
from string import digits, ascii_lowercase, ascii_uppercase
import random
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("user.login", next_url=request.url))
        else:
            return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return "." in filename and filename.split(".", 1)[1] in ALLOWED_EXTENSIONS


def random_generator(len = 8):
    char = ascii_uppercase + ascii_lowercase + digits
    return "".join(random.sample(char, len))

# secure_filename() 기능의 함수
def check_filename(filename):
    reg = re.compile("[^A-Za-z0-9-_.가-힝]")
    for s in os.path.sep, os.path.altsep:
        if s:
            filename = filename.replace(s, ' ')
            filename = str(reg.sub('', '_'.join(filename.split()))).strip("._")
    return filename

# 파일의 확장자를 구하는 함수
def get_extension(filename):
    extension_name = filename.split(".", 1)[1]
    return extension_name


def hash_password(password):
    return generate_password_hash(password)

def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)