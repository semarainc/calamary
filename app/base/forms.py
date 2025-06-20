# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
Copyright (c) 2021 - Semara (semarainc)
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, HiddenField
from wtforms.validators import InputRequired, Email, DataRequired

## login and registration

class LoginForm(FlaskForm):
    username = StringField    ('Username', id='username_login'   , validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login'        , validators=[DataRequired()])
    remember = BooleanField('remember', id='remember'        , validators=[])

class CreateAccountForm(FlaskForm):
    username = StringField('Username'     , id='username_create' , validators=[DataRequired()])
    email    = StringField('Email'        , id='email_create'    , validators=[DataRequired(), Email()])
    password = PasswordField('Password' , id='pwd_create'      , validators=[DataRequired()])

class CreateVoterForm(FlaskForm):
    nama     = StringField('Nama'      , validators=[DataRequired()])
    nim      = StringField('Nim'     , validators=[DataRequired()])
    alamat   = TextAreaField('Alamat'      , validators=[DataRequired()])
    angkatan = StringField('Angkatan'     , validators=[DataRequired()])
    semester = StringField('Semester'     , validators=[DataRequired()])
    prodi    = SelectField('Prodi', choices=[("0", "--Pilih Prodi--"), ('Kedokteran', 'Kedokteran'), ('Kebidanan', 'Kebidanan')], validators=[DataRequired()], default="0")
    username = StringField('Username'      , validators=[DataRequired()])
    email    = StringField('Email'            , validators=[DataRequired(), Email()])
    password = PasswordField('Password'      , validators=[DataRequired()])

class EditVoterForm(FlaskForm):
    id       = HiddenField('id')
    nama     = StringField('Nama'      , validators=[DataRequired()])
    nim      = StringField('Nim'     , validators=[DataRequired()])
    alamat   = TextAreaField('Alamat'      , validators=[DataRequired()])
    angkatan = StringField('Angkatan'     , validators=[DataRequired()])
    semester = StringField('Semester'     , validators=[DataRequired()])
    prodi    = SelectField('Prodi', choices=[('Kedokteran', 'Kedokteran'), ('Kebidanan', 'Kebidanan')], validators=[DataRequired()])
    username = StringField('Username'      , validators=[DataRequired()])
    email    = StringField('Email'            , validators=[DataRequired(), Email()])
    password = PasswordField('Password'      , validators=[])

class CreateCandidateForm(FlaskForm):
    nomorurut= StringField('NomorUrut'      , validators=[DataRequired()])
    nama     = StringField('Nama'      , validators=[DataRequired()])
    nim      = StringField('Nim'     , validators=[DataRequired()])
    angkatan = StringField('Angkatan'     , validators=[DataRequired()])
    semester = StringField('Semester'     , validators=[DataRequired()])
    alamat   = TextAreaField('Alamat'      , validators=[DataRequired()])
    prodi    = SelectField('Prodi', choices=[("0", "--Pilih Prodi--"), ('Kedokteran', 'Kedokteran'), ('Kebidanan', 'Kebidanan')], validators=[DataRequired()], default="0")
    artikel = TextAreaField('Artikel'      , validators=[])
    foto = FileField('File')

class EditCandidateForm(FlaskForm):
    id       = HiddenField('id')
    nomorurut= StringField('NomorUrut'      , validators=[DataRequired()])
    nama     = StringField('Nama'      , validators=[DataRequired()])
    nim      = StringField('Nim'     , validators=[DataRequired()])
    angkatan = StringField('Angkatan'     , validators=[DataRequired()])
    semester = StringField('Semester'     , validators=[DataRequired()])
    alamat   = TextAreaField('Alamat'      , validators=[DataRequired()])
    prodi    = SelectField('Prodi', choices=[("0", "--Pilih Prodi--"), ('Kedokteran', 'Kedokteran'), ('Kebidanan', 'Kebidanan')], validators=[DataRequired()], default="0")
    artikel = TextAreaField('Artikel'      , validators=[])
    foto = FileField('File')

class TimerRekapForm(FlaskForm):
    angkatan = StringField    ('Angkatan'   , validators=[DataRequired()])
    semester = StringField ('Semester'       , validators=[DataRequired()])
    prodi    = SelectField('Prodi', choices=[("0", "--Pilih Prodi--"), ('Kedokteran', 'Kedokteran'), ('Kebidanan', 'Kebidanan')], validators=[DataRequired()], default="0")

class EditRekapForm(FlaskForm):
    id       = HiddenField('id')
    angkatan = StringField    ('Angkatan'   , validators=[DataRequired()])
    semester = StringField ('Semester'       , validators=[DataRequired()])