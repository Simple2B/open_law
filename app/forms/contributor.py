from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

from app import models as m


class AddContributorForm(FlaskForm):
    user_id = StringField("User ID", [DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            (member.value, name.capitalize())
            for name, member in m.BookContributor.Roles.__members__.items()
        ],
    )

    submit = SubmitField("Add Contributor")


class DeleteContributorForm(FlaskForm):
    user_id = StringField("User ID", [DataRequired()])

    submit = SubmitField("Delete Contributor")


class EditContributorRoleForm(FlaskForm):
    user_id = StringField("User ID", [DataRequired()])
    role = SelectField(
        "Role",
        choices=[
            (member.value, name.capitalize())
            for name, member in m.BookContributor.Roles.__members__.items()
        ],
    )

    submit = SubmitField("Edit Contributor")
