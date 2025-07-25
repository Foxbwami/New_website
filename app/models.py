from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from app.extensions import db

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), nullable=False, default="user")  # 'user' or 'admin'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None
        }

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    content = db.Column(db.Text)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Writer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255))

class SiteReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    stars = db.Column(db.Integer, nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    photo = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

    def is_admin(self):
        return hasattr(self, "role") and self.role == "admin"

    def is_writer(self):
        return hasattr(self, "role") and self.role == "writer"

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
     
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    method = db.Column(db.String(50))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PublicPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    level = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    writer_id = db.Column(db.Integer, db.ForeignKey("writer.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def calculate_price(word_count, level, deadline):
    base_rate = 0.05
    urgency_multiplier = 2.0 if (deadline - datetime.utcnow()).days <= 1 else 1.0
    level_multiplier = {"Undergrad": 1.0, "Masters": 1.5, "PhD": 2.0}.get(level, 1.0)
    return word_count * base_rate * urgency_multiplier * level_multiplier

class OrderFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.Column(db.String(50))
    order_id = db.Column(db.Integer, nullable=True)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)