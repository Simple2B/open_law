from uuid import uuid4

from flask import current_app as Response

from app import models as m

TEST_ADMIN_NAME = "bob"
TEST_ADMIN_EMAIL = "bob@test.com"
TEST_ADMIN_PASSWORD = "password"


def create(username=TEST_ADMIN_NAME, password=TEST_ADMIN_PASSWORD):
    user = m.User(username=username)
    user.password = password
    user.save()
    return user


def login(
    client,
    username=TEST_ADMIN_NAME,
    password=TEST_ADMIN_PASSWORD,
    create_user_if_not_exists=True,
):
    user = m.User.query.filter_by(username=username).first()
    if create_user_if_not_exists and not user:
        user = create(username, password)

    response = client.post(
        "/login", data=dict(user_id=username, password=password), follow_redirects=True
    )
    return response, user


def logout(client):
    return client.get("/logout", follow_redirects=True)


def create_test_book(client):
    book = create_book(client)
    collection, _ = create_collection(client, book.id)
    section, _ = create_section(client, book.id, collection.id)
    interpretation, _ = create_interpretation(client, book.id, section.id)
    create_comment(client, book.id, interpretation.id)

    return book


def check_if_nested_book_entities_is_deleted(book: m.Book, is_deleted: bool = True):
    for version in book.versions:
        version: m.BookVersion
        assert version.is_deleted == is_deleted

        check_if_nested_version_entities_is_deleted(version)


def check_if_nested_version_entities_is_deleted(
    book_version: m.BookVersion, is_deleted: bool = True
):
    root_collection: m.Collection = book_version.root_collection
    assert root_collection.is_deleted == is_deleted
    for collection in root_collection.children:
        collection: m.Collection
        assert collection.is_deleted == is_deleted

        check_if_nested_collection_entities_is_deleted(collection)


def check_if_nested_collection_entities_is_deleted(
    collection: m.Collection, is_deleted: bool = True
):
    for section in collection.sections:
        section: m.Section
        assert section.is_deleted == is_deleted
        check_if_nested_section_entities_is_deleted(section, is_deleted)


def check_if_nested_section_entities_is_deleted(
    section: m.Section, is_deleted: bool = True
):
    for interpretation in section.interpretations:
        interpretation: m.Interpretation
        assert interpretation.is_deleted == is_deleted

        check_if_nested_interpretation_entities_is_deleted(interpretation, is_deleted)


def check_if_nested_interpretation_entities_is_deleted(
    interpretation: m.Interpretation, is_deleted: bool = True
):
    for comment in interpretation.comments:
        comment: m.Comment
        assert comment.is_deleted == is_deleted


def check_if_nested_comment_entities_is_deleted(
    comment: m.Comment, is_deleted: bool = True
):
    for child in comment.children:
        child: m.Comment
        assert child.is_deleted == is_deleted


# book entities:


def create_book(client):
    random_id = str(uuid4())
    BOOK_NAME = f"TBook {random_id}"
    response: Response = client.post(
        "/book/create",
        data=dict(label=BOOK_NAME),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Book added!" in response.data

    book: m.Book = m.Book.query.filter_by(label=BOOK_NAME).first()

    assert book
    assert book.versions
    assert len(book.versions) == 1
    assert book.access_groups
    assert len(book.access_groups) == 2

    root_collection: m.Collection = book.active_version.collections[0]
    assert root_collection
    assert root_collection.access_groups
    assert len(root_collection.access_groups) == 2

    return book


def add_contributor(client, book_id, user_id, role):
    response: Response = client.post(
        f"/book/{book_id}/add_contributor",
        data=dict(user_id=user_id, role=role),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Contributor was added!" in response.data


def create_collection(client, book_id):
    random_id = str(uuid4())
    LABEL = f"TCollection {random_id}"
    response: Response = client.post(
        f"/book/{book_id}/create_collection",
        data=dict(label=LABEL),
        follow_redirects=True,
    )

    assert response.status_code == 200
    collection: m.Collection = m.Collection.query.filter_by(label=LABEL).first()

    return collection, response


def create_sub_collection(client, book_id, collection_id):
    random_id = str(uuid4())
    LABEL = f"TCollection {random_id}"
    response: Response = client.post(
        f"/book/{book_id}/{collection_id}/create_sub_collection",
        data=dict(label=LABEL),
        follow_redirects=True,
    )

    assert response.status_code == 200
    collection: m.Collection = m.Collection.query.filter_by(label=LABEL).first()

    return collection, response


def create_section(client, book_id, collection_id):
    random_id = str(uuid4())
    LABEL = f"TSection {random_id}"
    response: Response = client.post(
        f"/book/{book_id}/{collection_id}/create_section",
        data=dict(collection_id=collection_id, label=LABEL),
        follow_redirects=True,
    )

    section: m.Section = m.Section.query.filter_by(
        label=LABEL, collection_id=collection_id
    ).first()
    return section, response


def create_interpretation(client, book_id, section_id):
    random_id = str(uuid4())
    LABEL = f"TInterpretation {random_id}"
    response: Response = client.post(
        f"/book/{book_id}/{section_id}/create_interpretation",
        data=dict(section_id=section_id, text=LABEL),
        follow_redirects=True,
    )
    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        section_id=section_id, text=LABEL
    ).first()
    return interpretation, response


def create_comment(client, book_id, interpretation_id):
    random_id = str(uuid4())
    TEXT = f"TComment {random_id}"
    response: Response = client.post(
        f"/book/{book_id}/{interpretation_id}/create_comment",
        data=dict(
            text=TEXT,
            interpretation_id=interpretation_id,
        ),
        follow_redirects=True,
    )
    comment: m.Comment = m.Comment.query.filter_by(text=TEXT).first()
    return comment, response
