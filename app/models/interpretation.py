from flask_login import current_user

from app import db, models as m
from app.models.utils import BaseModel


class Interpretation(BaseModel):
    __tablename__ = "interpretations"

    text = db.Column(db.Text, unique=False, nullable=False)
    plain_text = db.Column(db.Text, unique=False)
    approved = db.Column(db.Boolean, default=False)
    copy_of = db.Column(db.Integer, default=0, nullable=True)

    # Foreign keys
    user_id = db.Column(db.ForeignKey("users.id"))
    section_id = db.Column(db.ForeignKey("sections.id"))
    score = db.Column(db.Integer(), default=0)

    # Relationships
    user = db.relationship("User")
    section = db.relationship("Section")
    comments = db.relationship("Comment", viewonly=True, order_by="desc(Comment.id)")
    votes = db.relationship("InterpretationVote", viewonly=True)
    tags = db.relationship(
        "Tag",
        secondary="interpretation_tags",
        back_populates="interpretations",
    )
    access_groups = db.relationship(
        "AccessGroup",
        secondary="interpretations_access_groups",
    )  # access_groups related to current entity

    @property
    def vote_count(self):
        count = 0

        for vote in self.votes:
            if vote.positive:
                count += 1
                continue
            count -= 1

        return count

    @property
    def current_user_vote(self):
        for vote in self.votes:
            if vote.user_id == current_user.id:
                return vote.positive
        return None

    @property
    def active_comments(self):
        return [comment for comment in self.comments if not comment.is_deleted]

    @property
    def book(self) -> m.Book:
        return self.section.version.book

    def __repr__(self):
        return f"<Interpretation: {self.id}>"
