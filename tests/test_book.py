from flask import current_app as Response
from flask.testing import FlaskClient, FlaskCliRunner

from app import models as m, db
from app.controllers.create_access_groups import create_moderator_group
from tests.utils import (
    add_contributor,
    create,
    login,
    logout,
    check_if_nested_book_entities_is_deleted,
    check_if_nested_collection_entities_is_deleted,
    check_if_nested_section_entities_is_deleted,
    check_if_nested_interpretation_entities_is_deleted,
    create_test_book,
    create_book,
    create_collection,
    create_section,
    create_sub_collection,
)


def test_create_edit_delete_book(client: FlaskClient):
    login(client)

    BOOK_NAME = "Test Book"

    # label len < 6
    response: Response = client.post(
        "/book/create",
        data=dict(
            label="123",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Label must be between 4 and 256 characters long." in response.data

    book: m.Book = m.Book.query.filter_by(label=BOOK_NAME).first()

    assert not book
    assert not m.Book.query.count()

    # label len > 256
    response: Response = client.post(
        "/book/create",
        data=dict(
            label="".join(["0" for _ in range(1025)]),
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Label must be between 4 and 256 characters long." in response.data

    book: m.Book = m.Book.query.filter_by(label=BOOK_NAME).first()

    assert not book
    assert not m.Book.query.count()

    response: Response = client.post(
        "/book/create",
        data=dict(
            label=BOOK_NAME,
        ),
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

    response: Response = client.post(
        "/book/999/edit",
        data=dict(
            book_id=999,
            label="Book 1",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Book not found!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/edit",
        data=dict(
            book_id=book.id,
            label=BOOK_NAME + " EDITED",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data
    book = db.session.get(m.Book, book.id)
    assert book.label != BOOK_NAME

    response: Response = client.post(
        f"/book/{book.id}/delete",
        data=dict(
            book_id=book.id,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data
    book = db.session.get(m.Book, book.id)
    assert book.is_deleted
    check_if_nested_book_entities_is_deleted(book)


def test_add_delete_contributor(client: FlaskClient):
    _, moderator = login(client, "Moderator", "test")
    moderators_book = create_book(client)
    logout(client)
    _, user = login(client)
    user: m.User

    response: Response = client.post(
        f"/book/{moderators_book.id}/add_contributor",
        data=dict(user_id=moderator.id, role=m.BookContributor.Roles.MODERATOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"You do not have permission" in response.data

    book = create_book(client)

    response: Response = client.post(
        f"/book/{book.id}/add_contributor",
        data=dict(user_id=moderator.id, role=m.BookContributor.Roles.MODERATOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Contributor was added!" in response.data
    moderator: m.User = db.session.get(m.User, moderator.id)
    assert moderator.access_groups
    for access_group in moderator.access_groups:
        access_group: m.AccessGroup
        assert access_group.book_id == book.id

    response: Response = client.post(
        f"/book/{book.id}/add_contributor",
        data=dict(user_id=moderator.id, role=m.BookContributor.Roles.MODERATOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Already exists!" in response.data

    contributor: m.BookContributor = m.BookContributor.query.filter_by(
        user=moderator, book=book
    ).first()
    assert contributor.role == m.BookContributor.Roles.MODERATOR
    assert len(book.contributors) == 1

    editor = m.User(username="Editor", password="test").save()
    response: Response = client.post(
        f"/book/{book.id}/add_contributor",
        data=dict(user_id=editor.id, role=m.BookContributor.Roles.EDITOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Contributor was added!" in response.data

    contributor: m.BookContributor = m.BookContributor.query.filter_by(
        user=editor, book=book
    ).first()
    assert contributor.role == m.BookContributor.Roles.EDITOR
    assert len(book.contributors) == 2

    contributor_to_delete = m.BookContributor.query.filter_by(
        user_id=moderator.id, book_id=book.id
    ).first()

    assert moderator.access_groups
    response: Response = client.post(
        f"/book/{book.id}/delete_contributor",
        data=dict(user_id=contributor_to_delete.user_id),
        follow_redirects=True,
    )
    moderator: m.User = db.session.get(m.User, moderator.id)
    assert not moderator.access_groups

    assert response.status_code == 200
    assert b"Success!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/delete_contributor",
        data=dict(user_id=contributor_to_delete.user_id),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Does not exists!" in response.data

    response: Response = client.post(
        f"/book/{123}/add_contributor",
        data=dict(user_id=1, role=m.BookContributor.Roles.MODERATOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Book not found!" in response.data


def test_edit_contributor_role(client: FlaskClient, runner: FlaskCliRunner):
    _, user = login(client)
    user: m.User

    book = create_book(client)

    book.user_id = user.id
    book.save()

    contributor = create("test", "text")
    add_contributor(client, book.id, contributor.id, m.BookContributor.Roles.MODERATOR)

    contributors_len = len(book.contributors)
    assert contributors_len

    contributor_edit = book.contributors[0]

    assert contributor_edit.role == m.BookContributor.Roles.MODERATOR

    response: Response = client.post(
        f"/book/{book.id}/edit_contributor_role",
        data=dict(
            user_id=contributor_edit.user_id,
            role=m.BookContributor.Roles.MODERATOR.value,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    moderator = m.User(username="Moderator", password="test").save()

    logout(client)
    login(client, "Moderator", "test")
    moderators_book: m.Book = create_book(client)
    logout(client)
    login(client)

    response: Response = client.post(
        f"/book/{moderators_book.id}/add_contributor",
        data=dict(user_id=moderator.id, role=m.BookContributor.Roles.MODERATOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"You do not have permission" in response.data

    response: Response = client.post(
        "/book/999/add_contributor",
        data=dict(user_id=moderator.id, role=m.BookContributor.Roles.MODERATOR),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Book not found!" in response.data


def test_crud_collection(client: FlaskClient):
    _, user = login(client)
    user: m.User
    book = create_test_book(client)

    response: Response = client.post(
        f"/book/{book.id}/create_collection",
        data=dict(label="Test Collection #1 Label", about="Test Collection #1 About"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/create_collection",
        data=dict(label="Test Collection #1 Label", about="Test Collection #1 About"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection label must be unique!" in response.data

    response: Response = client.post(
        "/book/999/create_collection",
        data=dict(label="Test Collection #1 Label", about="Test Collection #1 About"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Book not found!" in response.data

    collection: m.Collection = m.Collection.query.filter_by(
        label="Test Collection #1 Label"
    ).first()

    assert collection
    assert collection.access_groups
    assert len(collection.access_groups) == 2
    for access_group in collection.access_groups:
        access_group: m.AccessGroup
        assert access_group.book_id == collection.version.book_id

    m.Collection(
        label="Test Collection #2 Label",
        version_id=collection.version_id,
        parent_id=collection.parent_id,
    ).save()

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/edit",
        data=dict(
            label="Test Collection #2 Label",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection label must be unique!" in response.data

    new_label = "Test Collection #1 Label(edited)"
    new_about = "Test Collection #1 About(edited)"

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/edit",
        data=dict(
            label=new_label,
            about=new_about,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    response: Response = client.post(
        f"/book/999/{collection.id}/edit",
        data=dict(label="Test Collection #1 Label", about="Test Collection #1 About"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Book not found!" in response.data

    edited_collection: m.Collection = m.Collection.query.filter_by(
        label=new_label, about=new_about
    ).first()
    assert edited_collection

    response: Response = client.post(
        f"/book/{book.id}/999/edit",
        data=dict(
            label=new_label,
            about=new_about,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    deleted_collection: m.Collection = db.session.get(m.Collection, collection.id)
    assert deleted_collection.is_deleted
    check_if_nested_collection_entities_is_deleted(deleted_collection)

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    response: Response = client.post(
        f"/book/999/{collection.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Book not found!" in response.data


def test_crud_subcollection(client: FlaskClient):
    _, user = login(client)
    user: m.User

    book = create_test_book(client)

    collection, _ = create_collection(client, book.id)
    leaf_collection, _ = create_sub_collection(client, book.id, collection.id)
    leaf_collection.is_leaf = True
    leaf_collection.save()

    response: Response = client.post(
        f"/book/999/{leaf_collection.id}/create_sub_collection",
        data=dict(
            label="Test SubCollection #1 Label", about="Test SubCollection #1 About"
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Book not found!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{leaf_collection.id}/create_sub_collection",
        data=dict(
            label="Test SubCollection #1 Label", about="Test SubCollection #1 About"
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"You can't create subcollection for this collection" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/create_sub_collection",
        data=dict(
            label="Test SubCollection #1 Label", about="Test SubCollection #1 About"
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/create_sub_collection",
        data=dict(
            label="Test SubCollection #1 Label", about="Test SubCollection #1 About"
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection label must be unique!" in response.data

    sub_collection: m.Collection = m.Collection.query.filter_by(
        label="Test SubCollection #1 Label"
    ).first()
    assert sub_collection
    assert not sub_collection.is_leaf
    assert sub_collection.parent_id == collection.id

    assert sub_collection.access_groups
    assert len(sub_collection.access_groups) == 2
    for access_group in sub_collection.access_groups:
        access_group: m.AccessGroup
        assert access_group.book_id == sub_collection.version.book_id

    m.Collection(
        label="Test SubCollection #2 Label",
        version_id=collection.version_id,
        parent_id=collection.id,
    ).save()

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/edit",
        data=dict(
            label="Test SubCollection #2 Label",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection label must be unique!" in response.data

    new_label = "Test SubCollection #1 Label(edited)"
    new_about = "Test SubCollection #1 About(edited)"

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/edit",
        data=dict(
            label=new_label,
            about=new_about,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    edited_collection: m.Collection = m.Collection.query.filter_by(
        label=new_label, about=new_about
    ).first()
    assert edited_collection

    response: Response = client.post(
        f"/book/{book.id}/9999/edit",
        data=dict(
            label=new_label,
            about=new_about,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    deleted_collection: m.Collection = db.session.get(m.Collection, sub_collection.id)
    assert deleted_collection.is_deleted
    check_if_nested_collection_entities_is_deleted(deleted_collection)

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data


def test_crud_sections(client: FlaskClient, runner: FlaskCliRunner):
    _, user = login(client)
    user: m.User

    book = create_test_book(client)
    collection, _ = create_collection(client, book.id)
    sub_collection, _ = create_sub_collection(client, book.id, collection.id)

    response: Response = client.post(
        f"/book/{book.id}/{collection.id}/create_section",
        data=dict(
            collection_id=collection.id,
            label="Test Section",
            about="Test Section #1 About",
        ),
        follow_redirects=True,
    )
    assert b"You can't create section for this collection" in response.data

    label_1 = "Test Section #1 Label"
    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/create_section",
        data=dict(
            collection_id=sub_collection.id,
            label=label_1,
            about="Test Section #1 About",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    section: m.Section = m.Section.query.filter_by(
        label=label_1, collection_id=sub_collection.id
    ).first()
    assert section
    assert section.collection_id == sub_collection.id
    assert section.version_id == book.active_version.id
    assert not section.interpretations

    assert section.access_groups
    assert len(section.access_groups) == 2
    for access_group in section.access_groups:
        access_group: m.AccessGroup
        assert access_group.book_id == section.version.book_id

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/create_section",
        data=dict(
            collection_id=sub_collection.id,
            label=label_1,
            about="Test Section #1 About",
        ),
        follow_redirects=True,
    )
    assert b"Section label must be unique!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/create_section",
        data=dict(
            collection_id=sub_collection.id,
            label=label_1,
            about="Test Section #1 About",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    section: m.Section = m.Section.query.filter_by(
        label=label_1, collection_id=sub_collection.id
    ).first()
    assert section
    assert section.collection_id == sub_collection.id
    assert section.version_id == book.active_version.id
    assert not section.interpretations

    response: Response = client.post(
        f"/book/{book.id}/{sub_collection.id}/create_section",
        data=dict(
            collection_id=sub_collection.id,
            label=label_1,
            about="Test Section #1 About",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section label must be unique!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/999/create_section",
        data=dict(
            collection_id=999,
            label=label_1,
            about="Test Section #1 About",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/999/create_section",
        data=dict(collection_id=999, label=label_1, about="Test Section #1 About"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    # edit

    m.Section(
        label="Test",
        collection_id=sub_collection.id,
        version_id=book.active_version.id,
    ).save()

    m.Section(
        label="Test",
        collection_id=sub_collection.id,
        version_id=book.active_version.id,
    ).save()

    section: m.Section = m.Section.query.filter_by(
        label=label_1, collection_id=sub_collection.id
    ).first()

    response: Response = client.post(
        f"/book/{book.id}/{section.id}/edit_section",
        data=dict(
            section_id=section.id,
            label="Test",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section label must be unique!" in response.data

    new_label = "Test Section #1 Label(edited)"
    new_about = "Test Section #1 About(edited)"

    response: Response = client.post(
        f"/book/{book.id}/{section.id}/edit_section",
        data=dict(section_id=section.id, label=new_label, about=new_about),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Success!" in response.data

    edited_section: m.Section = m.Section.query.filter_by(
        label=new_label, id=section.id
    ).first()
    assert edited_section

    #
    section_2: m.Section = m.Section.query.filter_by(
        label="Test Section #1 Label(edited)", collection_id=sub_collection.id
    ).first()
    response: Response = client.post(
        f"/book/{book.id}/{section_2.id}/edit_section",
        data=dict(
            section_id=section_2.id,
            label="Test",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section label must be unique!" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{section_2.id}/edit_section",
        data=dict(section_id=section_2.id, label=new_label, about=new_about),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Success!" in response.data

    edited_section: m.Section = m.Section.query.filter_by(
        label=new_label, id=section_2.id
    ).first()
    assert edited_section

    response: Response = client.post(
        f"/book/{book.id}/999/edit_section",
        data=dict(section_id=section_2.id, label=new_label, about=new_about),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/{section.id}/delete_section",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    deleted_section: m.Section = db.session.get(m.Section, section.id)
    assert deleted_section.is_deleted
    check_if_nested_section_entities_is_deleted(deleted_section)

    response: Response = client.post(
        f"/book/{book.id}/{section_2.id}/delete_section",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    deleted_section: m.Section = db.session.get(m.Section, section_2.id)
    assert deleted_section.is_deleted
    check_if_nested_section_entities_is_deleted(deleted_section)

    response: Response = client.post(
        f"/book/{book.id}/999/delete_section",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section not found" in response.data


def test_crud_interpretation(client: FlaskClient):
    _, user = login(client)
    user: m.User
    book = create_test_book(client)

    collection, _ = create_collection(client, book.id)
    section_in_collection, _ = create_section(client, book.id, collection.id)

    collection, _ = create_collection(client, book.id)
    sub_collection, _ = create_sub_collection(client, book.id, collection.id)
    section_in_subcollection, _ = create_section(client, book.id, sub_collection.id)

    text_1 = "Test Interpretation #1 Text"

    response: Response = client.post(
        f"/book/{book.id}/{section_in_subcollection.id}/create_interpretation",
        data=dict(section_id=section_in_subcollection.id, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        section_id=section_in_subcollection.id, text=text_1
    ).first()
    assert interpretation
    assert interpretation.section_id == section_in_subcollection.id
    assert not interpretation.comments

    assert interpretation.access_groups
    assert len(interpretation.access_groups) == 2
    for access_group in interpretation.access_groups:
        access_group: m.AccessGroup
        assert access_group.book_id == interpretation.section.version.book_id

    response: Response = client.post(
        f"/book/{book.id}/{section_in_collection.id}/create_interpretation",
        data=dict(section_id=section_in_collection.id, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        text=text_1, section_id=section_in_collection.id
    ).first()
    assert interpretation
    assert interpretation.section_id == section_in_collection.id
    assert not interpretation.comments

    response: Response = client.post(
        f"/book/{book.id}/999/create_section",
        data=dict(collection_id=999, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/999/create_interpretation",
        data=dict(collection_id=999, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/888/create_interpretation",
        data=dict(collection_id=999, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section not found" in response.data

    # edit

    i_1 = m.Interpretation(
        text="Test", section_id=section_in_collection.id, user_id=user.id
    ).save()

    i_2 = m.Interpretation(
        text="Test",
        section_id=section_in_subcollection.id,
    ).save()

    group = create_moderator_group(book.id)
    m.InterpretationAccessGroups(
        interpretation_id=i_1.id, access_group_id=group.id
    ).save()
    m.InterpretationAccessGroups(
        interpretation_id=i_2.id, access_group_id=group.id
    ).save()

    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        section_id=section_in_collection.id
    ).first()

    new_text = "Test Interpretation #1 Text(edited)"

    response: Response = client.post(
        f"/book/{book.id}/{interpretation.id}/edit_interpretation",
        data=dict(
            interpretation_id=interpretation.id,
            text=new_text,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Success!" in response.data

    edited_interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        text=new_text, id=interpretation.id
    ).first()
    assert edited_interpretation

    response: Response = client.post(
        f"/book/{book.id}/999/edit_interpretation",
        data=dict(
            interpretation_id="999",
            text=new_text,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Interpretation not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/999/delete_interpretation",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Interpretation not found" in response.data

    response: Response = client.post(
        (
            f"/book/{book.id}/{section_in_subcollection.interpretations[0].id}/delete_interpretation"
        ),
        data=dict(interpretation_id=section_in_subcollection.interpretations[0].id),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Success!" in response.data

    deleted_interpretation: m.Interpretation = db.session.get(
        m.Interpretation, section_in_subcollection.interpretations[0].id
    )
    assert deleted_interpretation.is_deleted
    check_if_nested_interpretation_entities_is_deleted(deleted_interpretation)


def test_crud_comment(client: FlaskClient, runner: FlaskCliRunner):
    _, user = login(client)
    user: m.User

    # add dummmy data
    runner.invoke(args=["db-populate"])

    book: m.Book = create_book(client)
    book.user_id = user.id
    book.save()

    collection, _ = create_collection(client, book.id)
    leaf_collection, _ = create_sub_collection(client, book.id, collection.id)
    create_section(client, book.id, leaf_collection.id)

    collection, _ = create_collection(client, book.id)
    sub_collection, _ = create_sub_collection(client, book.id, collection.id)
    section_in_subcollection, _ = create_section(client, book.id, sub_collection.id)

    group = create_moderator_group(book.id)
    m.SectionAccessGroups(
        section_id=section_in_subcollection.id, access_group_id=group.id
    ).save()

    label_1 = "Test Interpretation #1 Label"
    text_1 = "Test Interpretation #1 Text"

    response: Response = client.post(
        f"/book/{book.id}/{section_in_subcollection.id}/create_interpretation",
        data=dict(section_id=section_in_subcollection.id, label=label_1, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        section_id=section_in_subcollection.id
    ).first()
    assert interpretation
    assert interpretation.section_id == section_in_subcollection.id
    assert not interpretation.comments

    comment_text = "Some comment text"

    response: Response = client.post(
        f"/book/{book.id}/{interpretation.id}/create_comment",
        data=dict(
            text=comment_text,
            interpretation_id=interpretation.id,
        ),
        follow_redirects=True,
    )

    assert response
    assert response.status_code == 200
    assert b"Success" in response.data
    assert str.encode(comment_text) in response.data

    comment: m.Comment = m.Comment.query.filter_by(text=comment_text).first()
    assert comment

    new_text = "Some new text"

    # edit
    response: Response = client.post(
        f"/book/{book.id}/{interpretation.id}/comment_edit",
        data=dict(
            text=new_text,
            interpretation_id=interpretation.id,
            comment_id=comment.id,
        ),
        follow_redirects=True,
    )

    assert response
    assert response.status_code == 200
    assert b"Success" in response.data
    assert str.encode(new_text) in response.data
    assert str.encode(comment_text) not in response.data

    # delete
    response: Response = client.post(
        f"/book/{book.id}/{interpretation.id}/comment_delete",
        data=dict(
            text=comment_text,
            interpretation_id=interpretation.id,
            comment_id=comment.id,
        ),
        follow_redirects=True,
    )

    assert response
    assert response.status_code == 200
    assert b"Success" in response.data
    assert str.encode(comment_text) not in response.data


def test_access_to_settings_page(client: FlaskClient):
    _, user = login(client)

    book_1 = create_book(client)

    book_2 = create_book(client)

    response: Response = client.get(
        f"/book/{book_1.id}/settings",
        follow_redirects=True,
    )

    assert response.status_code == 200

    response: Response = client.get(
        f"/book/{book_2.id}/settings",
        follow_redirects=True,
    )

    assert response.status_code == 200

    logout(client)

    response: Response = client.get(
        f"/book/{book_2.id}/settings",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"You do not have permission" in response.data


def test_interpretation_in_home_last_inter_section(
    client: FlaskClient, runner: FlaskCliRunner
):
    login(client)

    book: m.Book = create_book(client)

    collection, _ = create_collection(client, book.id)
    section_in_collection, _ = create_section(client, book.id, collection.id)

    collection, _ = create_collection(client, book.id)
    sub_collection, _ = create_sub_collection(client, book.id, collection.id)
    section_in_subcollection, _ = create_section(client, book.id, sub_collection.id)

    group = create_moderator_group(book.id)
    m.SectionAccessGroups(
        section_id=section_in_subcollection.id, access_group_id=group.id
    ).save()
    m.SectionAccessGroups(
        section_id=section_in_collection.id, access_group_id=group.id
    ).save()

    label_1 = "Test Interpretation no1 Label"
    text_1 = "Test Interpretation no1 Text"

    response: Response = client.post(
        f"/book/{book.id}/{section_in_subcollection.id}/create_interpretation",
        data=dict(section_id=section_in_subcollection.id, label=label_1, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        section_id=section_in_subcollection.id
    ).first()
    assert interpretation
    assert interpretation.section_id == section_in_subcollection.id
    assert not interpretation.comments

    response: Response = client.post(
        f"/book/{book.id}/{section_in_collection.id}/create_interpretation",
        data=dict(section_id=section_in_collection.id, label=label_1, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    interpretation: m.Interpretation = m.Interpretation.query.filter_by(
        section_id=section_in_collection.id
    ).first()
    assert interpretation
    assert interpretation.section_id == section_in_collection.id
    assert not interpretation.comments

    response: Response = client.post(
        f"/book/{book.id}/999/create_section",
        data=dict(collection_id=999, label=label_1, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Collection not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/999/create_interpretation",
        data=dict(collection_id=999, label=label_1, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section not found" in response.data

    response: Response = client.post(
        f"/book/{book.id}/888/create_interpretation",
        data=dict(collection_id=999, label=label_1, text=text_1),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Section not found" in response.data

    response: Response = client.get(
        "/home",
        follow_redirects=True,
    )

    assert response
    assert response.status_code == 200
    assert str.encode(text_1) in response.data
