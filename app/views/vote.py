from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app import models as m, db
from app.logger import log
from app.controllers.notification_producer import (
    interpretation_notification,
    comment_notification,
)

bp = Blueprint("vote", __name__, url_prefix="/vote")


@bp.route(
    "/interpretation/<int:interpretation_id>",
    methods=["POST"],
)
@login_required
def vote_interpretation(interpretation_id: int):
    interpretation: m.Interpretation = db.session.get(
        m.Interpretation, interpretation_id
    )
    if not interpretation:
        log(log.WARNING, "Interpretation with id [%s] not found", interpretation_id)
        return jsonify({"message": "Interpretation not found"}), 404

    vote: m.InterpretationVote = m.InterpretationVote.query.filter_by(
        user_id=current_user.id, interpretation_id=interpretation_id
    ).first()
    if vote:
        db.session.delete(vote)

    positive = request.json.get("positive") in ("true", True)

    if not vote or vote.positive != positive:
        vote: m.InterpretationVote = m.InterpretationVote(
            user_id=current_user.id,
            interpretation_id=interpretation_id,
            positive=positive,
        )
        log(
            log.INFO,
            "User [%s]. [%s] vote interpretation: [%s]",
            current_user,
            "Positive" if positive else "Negative",
            interpretation,
        )
        vote.save(False)
    else:
        log(
            log.INFO,
            "User [%s]. Remove [%s] vote for interpretation: [%s]",
            current_user,
            "positive" if positive else "negative",
            interpretation,
        )
    db.session.commit()
    interpretation.score = interpretation.vote_count
    interpretation.save()
    # notifications
    if current_user.id != interpretation.user_id:
        interpretation_notification(
            m.Notification.Actions.VOTE, interpretation_id, interpretation.user_id
        )

    return jsonify(
        {
            "vote_count": interpretation.vote_count,
            "current_user_vote": interpretation.current_user_vote,
        }
    )


@bp.route(
    "/comment/<int:comment_id>",
    methods=["POST"],
)
@login_required
def vote_comment(comment_id: int):
    comment: m.Comment = db.session.get(m.Comment, comment_id)
    if not comment:
        log(log.WARNING, "Comment with id [%s] not found", comment_id)
        return jsonify({"message": "Comment not found"}), 404

    vote: m.CommentVote = m.CommentVote.query.filter_by(
        user_id=current_user.id, comment_id=comment_id
    ).first()
    if vote:
        db.session.delete(vote)

    positive = request.json.get("positive") in ("true", True)

    if not vote or vote.positive != positive:
        vote: m.CommentVote = m.CommentVote(
            user_id=current_user.id,
            comment_id=comment_id,
            positive=positive,
        )
        log(
            log.INFO,
            "User [%s]. [%s] vote comment: [%s]",
            current_user,
            "Positive" if positive else "Negative",
            comment,
        )
        vote.save(False)
    else:
        log(
            log.INFO,
            "User [%s]. Remove [%s] vote for comment: [%s]",
            current_user,
            "positive" if positive else "negative",
            comment,
        )
    db.session.commit()
    # notifications
    if current_user.id != comment.user_id:
        comment_notification(m.Notification.Actions.VOTE, comment_id, comment.user_id)
    return jsonify(
        {
            "vote_count": comment.vote_count,
            "current_user_vote": comment.current_user_vote,
        }
    )
