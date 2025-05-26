from flask import (
    Flask, url_for, session,
    render_template, request, redirect
)
from flask_sqlalchemy import SQLAlchemy
from models import db, Place, User, Review, OperatingHours, Category
from datetime import datetime
from functools import wraps
from markupsafe import escape 

import os, urllib.parse, re, time
import bcrypt

import os
from dotenv import load_dotenv
      
application = Flask(__name__)
application.secret_key = os.getenv("SECRET_KEY")

DB_USER = os.environ.get("DB_USER")
DB_PW   = os.environ.get("DB_PW")
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")

application.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PW}@{DB_HOST}/{DB_NAME}"
)
#DB_PW = os.getenv("DB_PW", "")
#if not DB_PW:
#    raise ValueError("DB_PW 환경변수가 설정되지 않았습니다.")
#pw_quoted = urllib.parse.quote_plus(DB_PW)

application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(application)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@application.route("/initdb")
def init_db():
    if os.environ.get("FLASK_ENV") != "production":
        return "운영 환경에서 이 URL은 사용할 수 없습니다.", 403
    try:
        db.create_all()
        return "✅ 데이터베이스 초기화 완료!"
    except Exception as e:
        return f"❌ 오류 발생: {e}", 500


@application.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email    = request.form["email"]
        password = request.form["password"]

        errors = []

        if not username or len(username) < 2:
            errors.append("사용자명은 2자 이상이어야 합니다.")
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            errors.append("아이디는 영문자, 숫자, 밑줄(_)만 사용할 수 있습니다.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("유효한 이메일 주소를 입력하세요.")
        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[a-zA-Z]", password):
            errors.append("비밀번호는 8자 이상, 영문자와 숫자를 포함해야 합니다.")
        if username.lower() in password.lower():
            errors.append("비밀번호에 아이디를 포함할 수 없습니다.")

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            errors.append("이미 등록된 사용자명 또는 이메일입니다.")

        if errors:
            return render_template("signup.html", errors=errors,
                                   username=username, email=email)

        # 비밀번호 해싱 및 저장
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        new_user = User(username=username, email=email, password=hashed_pw.decode("utf-8"))
        db.session.add(new_user)
        db.session.commit()

        session["user_id"]  = new_user.user_id
        session["username"] = new_user.username
        return redirect(url_for("home"))
    return render_template("signup.html")

@application.route("/")
def home():
    is_logged_in = "user_id" in session
    user_id = session.get("user_id")
    username = session.get("username")
    review_count = Review.query.filter_by(user_id=user_id).count() if is_logged_in else 0

    keyword = request.args.get("q", "").strip()
    sort = request.args.get("sort", "rating")

    query = (
        db.session.query(
            Place.place_id,
            Place.name,
            db.func.coalesce(db.func.avg(Review.rating), 0).label("avg_rating")
        )
        .outerjoin(Review, Review.place_id == Place.place_id)
        .join(Category, Category.category_id == Place.category_id)
        .group_by(Place.place_id)
    )
    #검색 관련
    if keyword:
        query = query.filter(
            db.or_(
                Place.name.like(f"%{keyword}%"),
                Category.name.like(f"%{keyword}%")
            )
        )

    # 정렬
    if sort == "name":
        query = query.order_by(Place.name.asc())
    else:
        query = query.order_by(db.desc("avg_rating"))

    places = query.all()

    return render_template(
        "home.html",
        login=is_logged_in,
        userid=username,
        review_count=review_count,
        places=places
    )

@application.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or url_for("home")

    if request.method == "POST":
        username_in = request.form["loginId"]
        password_in = request.form["loginPw"]

        user = User.query.filter_by(username=username_in).first()

        if not user:
            time.sleep(1)
            places = (
                db.session.query(
                    Place.place_id,
                    Place.name,
                    db.func.coalesce(db.func.avg(Review.rating), 0).label("avg_rating")
                )
                .outerjoin(Review, Review.place_id == Place.place_id)
                .group_by(Place.place_id)
                .order_by(db.desc("avg_rating"))
                .all()
            )

            return render_template(
                "home.html",
                login=False,
                userid=None,
                review_count=0,
                places=places,
                error="가입되지 않은 사용자입니다."
            )
        
        if not bcrypt.checkpw(password_in.encode("utf-8"), user.password.encode("utf-8")):
            time.sleep(1)
            places = (
                db.session.query(
                    Place.place_id,
                    Place.name,
                    db.func.coalesce(db.func.avg(Review.rating), 0).label("avg_rating")
                )
                .outerjoin(Review, Review.place_id == Place.place_id)
                .group_by(Place.place_id)
                .order_by(db.desc("avg_rating"))
                .all()
            )

            return render_template(
                "home.html",
                login=False,
                userid=None,
                review_count=0,
                places=places,
                error="아이디 또는 비밀번호가 잘못되었습니다. <br>아이디와 비밀번호를 정확히 입력해 주세요."
            )

        # 로그인 성공
        session["user_id"]  = user.user_id
        session["username"] = user.username
        return redirect(next_url)

    return render_template("home.html", next=next_url)

@application.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("home"))

@application.route("/places")
def show_places():
    return home()

@application.route("/places/<int:place_id>")
def place_detail(place_id):
    place = Place.query.get_or_404(place_id)
    reviews = (
        Review.query
        .filter_by(place_id=place_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    hours = (
        OperatingHours.query
        .filter_by(place_id=place_id)
        .order_by(OperatingHours.id)
        .all()
    )
    return render_template(
        "place_detail.html",
        place=place,
        reviews=reviews,
        hours=hours
    )

#후기 관련
@application.route(
    "/places/<int:place_id>/reviews", methods=["GET", "POST"]
)
@login_required
def place_reviews(place_id):
    if request.method == "POST":
        rating  = float(request.form["rating"])
        content = request.form["content"]
        user_id = session["user_id"]
        content = request.form["content"].strip()

        content = escape(content.strip())

        if len(content) < 5 or len(content)> 500:
         return "후기 내용은 5자 이상 500자 이하로 입력해주세요.", 400

    
        new = Review(
            place_id=place_id,
            user_id=user_id,
            rating=rating,
            content=content
        )
        db.session.add(new)
        db.session.commit()
        return redirect(url_for("place_reviews", place_id=place_id))

    place = Place.query.get_or_404(place_id)
    reviews = (
        Review.query
        .filter_by(place_id=place_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    avg = (
        db.session.query(db.func.avg(Review.rating))
        .filter(Review.place_id==place_id)
        .scalar()
    ) or 0
    return render_template(
        "reviews.html",
        place=place,
        reviews=reviews,
        avg_rating=round(avg, 2)
    )

@application.route(
    "/reviews/<int:review_id>/edit", methods=["GET", "POST"]
)
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != session["user_id"]:
        return "권한이 없습니다.", 403

    if request.method == "POST":
        review.rating     = float(request.form["rating"])
        review.content    = request.form["content"]
        review.updated_at = datetime.now()
        db.session.commit()
        return redirect(
            url_for("place_reviews", place_id=review.place_id)
        )

    return render_template("edit_review.html", review=review)

@application.route("/reviews/<int:review_id>/delete")
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != session["user_id"]:
        return "권한이 없습니다.", 403
    place_id = review.place_id
    db.session.delete(review)
    db.session.commit()
    return redirect(url_for("place_reviews", place_id=place_id))

if __name__ == "__main__":
    with application.app_context():
        db.create_all()
    application.run(host="0.0.0.0", debug=False)
