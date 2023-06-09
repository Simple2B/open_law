from uuid import uuid4

from flask_login import UserMixin, AnonymousUserMixin
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.utils import BaseModel
from app.logger import log
from app import schema as s, models as m


def gen_uniq_id() -> str:
    return str(uuid4())


class User(BaseModel, UserMixin):
    __tablename__ = "users"

    username = db.Column(db.String(64), unique=True, default=gen_uniq_id)
    password_hash = db.Column(db.String(256), default="")
    is_activated = db.Column(db.Boolean, default=False)
    wallet_id = db.Column(db.String(64), nullable=True)
    avatar_img = db.Column(db.Text, nullable=True)
    is_super_user = db.Column(db.Boolean, default=False)

    # Relationships
    access_groups = db.relationship(
        "AccessGroup", secondary="users_access_groups", back_populates="users"
    )
    stars = db.relationship("Book", secondary="books_stars", back_populates="stars")
    books = db.relationship("Book")
    notifications = db.relationship("Notification")

    @hybrid_property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @classmethod
    def authenticate(cls, user_id, password):
        user = cls.query.filter(
            func.lower(cls.username) == func.lower(user_id),
        ).first()
        if not user:
            log(log.WARNING, "user:[%s] not found", user_id)

        if user is not None and check_password_hash(user.password, password):
            return user

    def __repr__(self):
        return f"<{self.id}: {self.username}>"

    @property
    def json(self):
        u = s.User.from_orm(self)
        return u.json()

    @property
    def contributions(self):
        contributions = m.Interpretation.query.filter_by(user_id=self.id).all()
        comments = m.Comment.query.filter_by(user_id=self.id).all()
        for comment in comments:
            if comment.parent:
                contributions.append(comment.parent.interpretation)
            else:
                contributions.append(comment.interpretation)
        return contributions

    @property
    def active_notifications(self):
        items = [
            notification
            for notification in self.notifications
            if not notification.is_read
        ]
        items.sort(key=lambda x: x.created_at)
        return items


class AnonymousUser(AnonymousUserMixin):
    pass
