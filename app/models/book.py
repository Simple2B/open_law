from flask_login import current_user
from sqlalchemy import and_

from app import db, models as m
from app.models.utils import BaseModel


class Book(BaseModel):
    __tablename__ = "books"

    label = db.Column(db.String(256), unique=False, nullable=False)
    about = db.Column(db.Text, unique=False, nullable=True)

    # Foreign keys
    user_id = db.Column(db.ForeignKey("users.id"))
    original_book_id = db.Column(db.ForeignKey("books.id"))

    # Relationships
    owner = db.relationship("User", viewonly=True)
    stars = db.relationship("User", secondary="books_stars", back_populates="stars")
    contributors = db.relationship("BookContributor")
    versions = db.relationship("BookVersion", order_by="asc(BookVersion.id)")
    list_access_groups = db.relationship(
        "AccessGroup"
    )  # all access_groups in current book(in nested entities)
    access_groups = db.relationship(
        "AccessGroup",
        secondary="books_access_groups",
    )  # access_groups related to current entity
    tags = db.relationship(
        "Tag",
        secondary="book_tags",
        back_populates="books",
    )
    forks = db.relationship(
        "Book",
        backref=db.backref("original_book", remote_side="Book.id"),
        viewonly=True,
        order_by="asc(Book.id)",
    )

    def __repr__(self):
        return f"<{self.id}: {self.label}>"

    @property
    def active_version(self):
        for version in self.versions:
            if version.is_active:
                return version
        raise ValueError("No active version found")

    @property
    def actual_versions(self):
        versions = (
            m.BookVersion.query.filter_by(
                is_deleted=False, book_id=self.id, is_active=False
            )
            .order_by(m.BookVersion.created_at.asc())
            .all()
        )
        return versions

    @property
    def active_forks(self):
        return [fork for fork in self.forks if not fork.is_deleted]

    @property
    def current_user_has_star(self):
        if current_user.is_authenticated:
            book_star: m.BookStar = m.BookStar.query.filter_by(
                user_id=current_user.id, book_id=self.id
            ).first()
            if book_star:
                return True

    @property
    def approved_comments(self):
        comments = (
            db.session.query(
                m.Comment,
            )
            .filter(
                and_(
                    m.BookVersion.id == self.active_version.id,
                    m.Section.version_id == m.BookVersion.id,
                    m.Collection.id == m.Section.collection_id,
                    m.Interpretation.section_id == m.Section.id,
                    m.Comment.interpretation_id == m.Interpretation.id,
                    m.Comment.approved.is_(True),
                    m.Comment.is_deleted.is_(False),
                    m.BookVersion.is_deleted.is_(False),
                    m.Interpretation.is_deleted.is_(False),
                    m.Section.is_deleted.is_(False),
                    m.Collection.is_deleted.is_(False),
                ),
            )
            .order_by(m.Comment.created_at.desc())
            .all()
        )

        return comments

    @property
    def approved_interpretations(self):
        interpretations = (
            db.session.query(
                m.Interpretation,
            )
            .filter(
                and_(
                    m.BookVersion.id == self.active_version.id,
                    m.Section.version_id == m.BookVersion.id,
                    m.Collection.id == m.Section.collection_id,
                    m.Interpretation.section_id == m.Section.id,
                    m.Interpretation.approved.is_(True),
                    m.BookVersion.is_deleted.is_(False),
                    m.Interpretation.is_deleted.is_(False),
                    m.Section.is_deleted.is_(False),
                    m.Collection.is_deleted.is_(False),
                ),
            )
            .order_by(m.Interpretation.created_at.desc())
            .all()
        )

        return interpretations

    @property
    def interpretations(self):
        interpretations = (
            db.session.query(
                m.Interpretation,
            )
            .filter(
                and_(
                    m.BookVersion.id == self.active_version.id,
                    m.Section.version_id == m.BookVersion.id,
                    m.Collection.id == m.Section.collection_id,
                    m.Interpretation.section_id == m.Section.id,
                    m.BookVersion.is_deleted.is_(False),
                    m.Interpretation.is_deleted.is_(False),
                    m.Section.is_deleted.is_(False),
                    m.Collection.is_deleted.is_(False),
                ),
            )
            .order_by(m.Interpretation.created_at.desc())
            .all()
        )

        return interpretations

    @property
    def contributors_users(self):
        return [contributors.user for contributors in self.contributors]
