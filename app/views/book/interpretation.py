from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    current_app,
)
from flask_login import login_required, current_user

from app.controllers import (
    register_book_verify_route,
    create_breadcrumbs,
    clean_html,
)
from app.controllers.notification_producer import interpretation_notification
from app.controllers.delete_nested_book_entities import (
    delete_nested_interpretation_entities,
)
from app.controllers.error_flashes import create_error_flash
from app import models as m, db, forms as f
from app.controllers.require_permission import require_permission
from app.controllers.tags import set_interpretation_tags
from app.logger import log
from .bp import bp


@bp.route("/<int:book_id>/<int:section_id>/interpretations", methods=["GET"])
def interpretation_view(
    book_id: int,
    section_id: int,
):
    book: m.Book = db.session.get(m.Book, book_id)
    if not book or book.is_deleted:
        log(log.WARNING, "Book with id [%s] not found", book_id)
        flash("Book not found", "danger")
        return redirect(url_for("book.my_library"))

    section: m.Section = db.session.get(m.Section, section_id)
    if not section:
        log(log.WARNING, "Section with id [%s] not found", section_id)
        flash("Section not found", "danger")
        return redirect(
            url_for(
                "book.collection_view",
                book_id=book_id,
            )
        )

    if section.copy_of:
        return redirect(
            url_for(
                "book.interpretation_view", book_id=book_id, section_id=section.copy_of
            )
        )

    breadcrumbs = create_breadcrumbs(
        book_id=book_id, section_id=section_id, collection_id=section.collection.id
    )
    return render_template(
        "book/interpretation_view.html",
        book=book,
        section=section,
        breadcrumbs=breadcrumbs,
    )


@bp.route("/<int:book_id>/<int:section_id>/create_interpretation", methods=["POST"])
@register_book_verify_route(bp.name)
@login_required
def interpretation_create(
    book_id: int,
    section_id: int,
):
    section: m.Section = db.session.get(m.Section, section_id)
    book: m.Book = db.session.get(m.Book, book_id)
    form = f.CreateInterpretationForm()
    redirect_url = url_for(
        "book.interpretation_view",
        book_id=book_id,
        section_id=section.id,
    )

    if form.validate_on_submit():
        text = form.text.data
        plain_text = clean_html(text).lower()
        tags = current_app.config["TAG_REGEX"].findall(text)
        for tag in tags:
            word = tag.lower().replace("#", "")
            plain_text = plain_text.replace(tag.lower(), word)

        interpretation: m.Interpretation = m.Interpretation(
            plain_text=plain_text,
            text=text,
            section_id=section_id,
            user_id=current_user.id,
        )
        log(
            log.INFO,
            "Create interpretation [%s]. Section: [%s]",
            interpretation,
            section,
        )
        interpretation.save()

        # access groups
        for access_group in interpretation.section.access_groups:
            m.InterpretationAccessGroups(
                interpretation_id=interpretation.id, access_group_id=access_group.id
            ).save()
        # -------------

        # notifications
        if current_user.id != book.owner.id:
            interpretation_notification(
                m.Notification.Actions.CREATE, interpretation.id, book.owner.id
            )
        # -------------

        tags = current_app.config["TAG_REGEX"].findall(text)
        set_interpretation_tags(interpretation, tags)

        flash("Success!", "success")
        return redirect(redirect_url)
    else:
        log(log.ERROR, "Interpretation create errors: [%s]", form.errors)
        create_error_flash(form)
        return redirect(redirect_url)


@bp.route(
    "/<int:book_id>/<int:interpretation_id>/edit_interpretation", methods=["POST"]
)
@register_book_verify_route(bp.name)
@login_required
def interpretation_edit(
    book_id: int,
    interpretation_id: int,
):
    interpretation: m.Interpretation = db.session.get(
        m.Interpretation, interpretation_id
    )
    if interpretation and interpretation.user_id != current_user.id:
        flash("You dont have permission to edit this interpretation", "danger")
        return redirect(url_for("book.collection_view", book_id=book_id))

    form = f.EditInterpretationForm()

    if form.validate_on_submit():
        text = form.text.data
        redirect_url = url_for(
            "book.interpretation_view",
            book_id=book_id,
            section_id=interpretation.section_id,
        )
        if not interpretation or interpretation.is_deleted:
            log(log.WARNING, "Interpretation with id [%s] not found", interpretation_id)
            flash("Interpretation not found", "danger")
            return redirect(
                url_for(
                    "book.interpretation_view",
                    book_id=book_id,
                    section_id=interpretation.section_id,
                )
            )
        plain_text = clean_html(text).lower()
        tags = current_app.config["TAG_REGEX"].findall(text)
        for tag in tags:
            word = tag.lower().replace("#", "")
            plain_text = plain_text.replace(tag.lower(), word)

        interpretation.plain_text = plain_text
        interpretation.text = text
        tags = current_app.config["TAG_REGEX"].findall(text)
        set_interpretation_tags(interpretation, tags)

        log(log.INFO, "Edit interpretation [%s]", interpretation.id)
        interpretation.save()

        flash("Success!", "success")
        return redirect(redirect_url)
    else:
        log(log.ERROR, "Interpretation edit errors: [%s]", form.errors)
        create_error_flash(form)
        return redirect(redirect_url)


@bp.route(
    "/<int:book_id>/<int:interpretation_id>/delete_interpretation", methods=["POST"]
)
@register_book_verify_route(bp.name)
@require_permission(
    entity_type=m.Permission.Entity.INTERPRETATION,
    access=[m.Permission.Access.D],
    entities=[m.Interpretation],
)
@login_required
def interpretation_delete(
    book_id: int,
    interpretation_id: int,
):
    form = f.DeleteInterpretationForm()
    interpretation: m.Interpretation = db.session.get(
        m.Interpretation, interpretation_id
    )
    if not interpretation or interpretation.is_deleted:
        log(log.WARNING, "Interpretation with id [%s] not found", interpretation_id)
        flash("Interpretation not found", "danger")
        return redirect(url_for("book.collection_view", book_id=book_id))
    form = f.DeleteInterpretationForm()
    if form.validate_on_submit():
        interpretation.is_deleted = True
        delete_nested_interpretation_entities(interpretation)
        log(log.INFO, "Delete interpretation [%s]", interpretation)
        interpretation.save()
        redirect_url = url_for(
            "book.interpretation_view",
            book_id=book_id,
            section_id=interpretation.section_id,
        )
        # notifications
        if current_user.id != interpretation.user_id:
            interpretation_notification(
                m.Notification.Actions.DELETE, interpretation.id, interpretation.user_id
            )
        # -------------

        flash("Success!", "success")
        return redirect(redirect_url)
    return redirect(
        url_for(
            "book.collection_view",
            book_id=book_id,
        )
    )


@bp.route("/<int:book_id>/<int:interpretation_id>/preview", methods=["GET"])
def qa_view(book_id: int, interpretation_id: int):
    book: m.Book = db.session.get(m.Book, book_id)
    if not book or book.is_deleted:
        log(log.INFO, "User: [%s] is not owner of book: [%s]", current_user, book)
        flash("Book not found!", "danger")
        return redirect(url_for("book.my_library"))

    interpretation: m.Interpretation = db.session.get(
        m.Interpretation, interpretation_id
    )
    if not interpretation or interpretation.is_deleted:
        log(log.WARNING, "Interpretation with id [%s] not found", interpretation_id)
        flash("Interpretation not found", "danger")
        return redirect(url_for("book.collection_view", book_id=book_id))
    if interpretation.copy_of:
        return redirect(
            url_for(
                "book.qa_view",
                book_id=book_id,
                interpretation_id=interpretation.copy_of,
            )
        )

    breadcrumbs = create_breadcrumbs(
        book_id=book_id,
        collection_id=interpretation.section.collection.id,
        section_id=interpretation.section.id,
    )
    return render_template(
        "book/qa_view.html",
        book=book,
        section=interpretation.section,
        interpretation=interpretation,
        breadcrumbs=breadcrumbs,
    )
