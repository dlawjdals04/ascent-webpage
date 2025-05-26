from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as PgEnum, func 

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    user_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username   = db.Column(db.String(50),  nullable=False)
    email      = db.Column(db.String(100), nullable=False, unique=True)
    password   = db.Column(db.String(255), nullable=False)
    is_admin   = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(50),  nullable=False)

class Place(db.Model):
    __tablename__ = 'place'
    place_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(100), nullable=False)
    address     = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    category    = db.relationship('Category', backref='places')

class OperatingHours(db.Model):
    __tablename__ = 'operatinghours'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    place_id    = db.Column(db.Integer, db.ForeignKey('place.place_id'))
    day_of_week = db.Column(
     PgEnum('MON','TUE','WED','THU','FRI','SAT','SUN', name='dayofweek_enum')
    )
    open_time   = db.Column(db.Time)
    close_time  = db.Column(db.Time)
    is_closed   = db.Column(db.Boolean, default=False)
    place       = db.relationship('Place', backref='hours')

class Review(db.Model):
    __tablename__ = 'review'
    review_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    place_id    = db.Column(db.Integer, db.ForeignKey('place.place_id'))
    user_id     = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    rating      = db.Column(db.Float)
    content     = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, server_default=func.now())
    updated_at  = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    place       = db.relationship('Place', backref='reviews')
    user        = db.relationship('User', backref='reviews')

class ReportedReview(db.Model):
    __tablename__ = 'reportedreview'
    report_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review_id   = db.Column(db.Integer, db.ForeignKey('review.review_id'))
    user_id     = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    reason      = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, server_default=func.now())
    review      = db.relationship('Review', backref='reports')
    user        = db.relationship('User')
