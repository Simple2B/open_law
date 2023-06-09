from sqlalchemy import func, text

from app import db
from app.models.utils import BaseModel
from app.controllers import create_breadcrumbs
from .interpretation import Interpretation
from .comment import Comment
from .interpretation_vote import InterpretationVote
from app.controllers.next_prev_section import recursive_move_down, recursive_move_up


class Section(BaseModel):
    __tablename__ = "sections"

    label = db.Column(db.String(256), unique=False, nullable=False)
    position = db.Column(db.Integer, default=-1, nullable=True)
    copy_of = db.Column(db.Integer, default=0, nullable=True)

    # Foreign keys
    collection_id = db.Column(db.ForeignKey("collections.id"))
    user_id = db.Column(db.ForeignKey("users.id"))
    version_id = db.Column(db.ForeignKey("book_versions.id"))

    # Relationships
    collection = db.relationship("Collection", viewonly=True)
    user = db.relationship("User", viewonly=True)
    version = db.relationship("BookVersion", viewonly=True)
    interpretations = db.relationship(
        "Interpretation", viewonly=True, order_by="desc(Interpretation.id)"
    )
    access_groups = db.relationship(
        "AccessGroup",
        secondary="sections_access_groups",
    )  # access_groups related to current entity
    tags = db.relationship(
        "Tag",
        secondary="section_tags",
        back_populates="sections",
    )

    @property
    def path(self):
        parent = self.collection
        grand_parent = parent.parent
        path = f"{self.version.book.label} / "
        if grand_parent.is_root:
            path += f"{parent.label} / "
        else:
            path += f"{grand_parent.label} / {parent.label} / "
        path += self.label
        return path

    @property
    def breadcrumbs_path(self):
        breadcrumbs_path = create_breadcrumbs(
            book_id=self.book_id, collection_id=self.collection.id
        )
        return breadcrumbs_path

    @property
    def book_id(self):
        _book_id = self.version.book_id
        return _book_id

    @property
    def sub_collection_id(self):
        parent = self.collection
        grand_parent = parent.parent
        if grand_parent.is_root:
            _sub_collection_id = parent.id
        else:
            _sub_collection_id = grand_parent.id
        return _sub_collection_id

    @property
    def active_interpretations(self):
        return [
            interpretation
            for interpretation in self.interpretations
            if not interpretation.is_deleted
        ]

    @property
    def approved_interpretation(self):
        interpretation = Interpretation.query.filter_by(
            approved=True, section_id=self.id, is_deleted=False
        ).first()

        if interpretation:
            return interpretation

        # most upvoted
        result = (
            db.session.query(
                Interpretation, func.count(Interpretation.votes).label("total_votes")
            )
            .join(InterpretationVote)
            .filter(
                Interpretation.section_id == self.id, Interpretation.is_deleted is False
            )
            .group_by(Interpretation.id)
            .order_by(text("total_votes DESC"))
        ).first()
        if result:
            return result[0]

        # oldest
        interpretation = (
            Interpretation.query.filter_by(section_id=self.id, is_deleted=False)
            .order_by(Interpretation.created_at)
            .first()
        )

        if interpretation:
            return interpretation

    @property
    def approved_comments(self):
        interpretation_ids = [
            interpretation.id for interpretation in self.interpretations
        ]
        comments = (
            Comment.query.filter_by(approved=True)
            .filter(Comment.interpretation_id.in_(interpretation_ids))
            .all()
        )

        return comments

    @property
    def next_section(self):
        section = (
            Section.query.filter(
                Section.collection_id == self.collection_id,
                Section.position > self.position,
            )
            .order_by(Section.position)
            .first()
        )
        if section:
            return section

        section = recursive_move_down(self.collection)
        return section

    @property
    def previous_section(self):
        section = (
            Section.query.filter(
                Section.collection_id == self.collection_id,
                Section.position < self.position,
            )
            .order_by(Section.position.desc())
            .first()
        )
        if section:
            return section

        section = recursive_move_up(self.collection)
        return section

    def __repr__(self):
        return f"<{self.id}: {self.label}>"
