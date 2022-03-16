from flask import Flask, request, render_template, redirect, url_for, abort
from flask import session, flash
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import time
import math
import os


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myweb"
app.config["SECRET_KEY"] = "abcd"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
csrf = CSRFProtect(app)
mongo = PyMongo(app)

BOARD_ATTACH_FILE_PATH = "C:\\myweb\\uploads"
BOARD_IMAGE_PATH = "C:\\myweb\\images"
ALLOWED_EXTENSIONS = set(["txt", "pdf", "jpg", "png", "jpeg", "gif", "JPG", "JPEG", "PNG", "GIF", "txt"])

app.config["BOARD_ATTACH_FILE_PATH"] = BOARD_ATTACH_FILE_PATH
app.config["BOARD_IMAGE_PATH"] = BOARD_IMAGE_PATH
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

if not os.path.exists(app.config["BOARD_IMAGE_PATH"]):
    os.mkdir(app.config["BOARD_IMAGE_PATH"])

if not os.path.exists(app.config["BOARD_ATTACH_FILE_PATH"]):
    os.mkdir(app.config["BOARD_ATTACH_FILE_PATH"])

from .common import login_required, allowed_file, random_generator, check_filename, get_extension, hash_password, check_password
from .filter import format_datetime
from . import user, board


app.register_blueprint(board.bp)
app.register_blueprint(user.bp)