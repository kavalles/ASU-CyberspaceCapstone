from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, Optional
from flask_wtf.file import FileField, FileRequired




class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	admin_or_not = BooleanField('Admin')
	submit = SubmitField('Sign up')

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
	password = PasswordField('Password', validators=[DataRequired()])
	admin_or_not = BooleanField('Admin')
	remember = BooleanField('Remember me')
	submit = SubmitField('login')

class SubmitForm(FlaskForm):
	artifact = StringField('Submit found artifacts here', validators=[DataRequired(), Length(min=1, max=100)])
	submit = SubmitField('Submit Artifact')

class FileUploadForm(FlaskForm):
	file = FileField('Upload Artifact List', validators=[FileRequired()])
	submit = SubmitField('Submit File')

class ChangePasswordForm(FlaskForm):
	oldPassword = PasswordField('Old Password', validators=[DataRequired(), Length(min=2, max=20)])
	newPassword = PasswordField('New Password', validators=[DataRequired()])
	confirm_newPassword = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('newPassword')])
	submit = SubmitField('Update Password')

class BulkRegisterForm(FlaskForm):
	howMany =  IntegerField('Number of Teams', validators=[DataRequired(), NumberRange(min=1, max=None)])
	submit = SubmitField('Register')

class ArtifactForm(FlaskForm):
	phaseId = StringField('Select Phase ID', validators=[DataRequired(), Length(min=1, max=100)])
	artifactName = StringField('Enter Artifact Name', validators=[DataRequired(), Length(min=1, max=100)])
	artifactType = StringField('Enter Artifact Type', validators=[DataRequired(), Length(min=1, max=100)])
	artifactString = StringField('Enter Artifact String', validators=[DataRequired(), Length(min=1, max=100)])
	difficulty = StringField('Enter Difficulty', validators=[DataRequired(), Length(min=1, max=100)])
	notes = StringField('Enter Notes', validators=[DataRequired(), Length(min=1, max=100)])
	submit = SubmitField('Upload Artifact')

class EditArtifactForm(FlaskForm):
	artifactId = StringField('Artifact ID',render_kw={'readOnly': True})
	phaseArtifactId = StringField('Enter Phase Artifact ID (Ensure phase+phaseArtifactId available in MSEL dropdown)')
	phaseName = StringField('Enter Phase Name')
	artifactName = StringField('Enter Artifact Name')
	artifactType = StringField('Enter Artifact Type')
	artifactString = StringField('Enter Artifact String')
	difficulty = StringField('Enter Difficulty')
	notes = StringField('Enter Notes')
	submit = SubmitField('Save Changes')
	selectSubmit = SubmitField('Select Artifact')

	
class PhaseManagementForm(FlaskForm):
	phaseName = StringField('Enter new phase name', validators=[Optional()])
	createSubmit = SubmitField('Create Phase',default='createSubmit')
	deleteSubmit = SubmitField('Delete Selected Phase',default='deleteSubmit')
	renameSubmit = SubmitField('Rename Selected Phase',default='renameSubmit')
	editPhaseName = StringField("Rename Selected Phase", validators=[Optional()])

