# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
Copyright (c) 2021 - Semara (semarainc)
"""

from flask_login import UserMixin
from sqlalchemy import LargeBinary, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from app import db, login_manager

from app.base.util import hash_pass

def AddAdmin(username="admin123", password="adminpemirafk123"):
    a = User(username=str(username).lower(), email="admin@pemira.com", password=password, role="admin")
    db.session.add(a)
    db.session.commit()
    print("****************************************************")
    print("[DEBUG] Creating Default Admin User")
    print("[DEBUG] Default Username: admin123")
    print("[DEBUG] Default Password: adminpemirafk123")
    print("****************************************************")

class User(db.Model, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(LargeBinary)
    password2 = Column(String)
    role = Column(String, nullable=False, default = 'voter')


    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
                print("------------!_!_!__!__!_!: ", value)

            if property == 'password':
                setattr(self, 'password2', value)
                value = hash_pass( value ) # we need bytes here (not plain str)
                print("---------> ", value)
                
            setattr(self, property, value)

    def __repr__(self):
        return str(f"User(id={self.id},username={self.username},email={self.email},password={self.password},role={self.role})")

class Voter(db.Model, UserMixin):

    __tablename__ = 'Voter'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    nama = Column(String)
    nim = Column(String, unique=True)
    prodi = Column(String)
    alamat = Column(String)
    angkatan = Column(Integer)
    semester = Column(Integer)
    email = Column(String, unique=True)


    def __repr__(self):
        return str(f"Voter(id={self.id},username={self.username},nama={self.nama},nim={self.nim},prodi={self.prodi}, alamat={self.alamat},angkatan={self.angkatan},semester={self.semester} email={self.email})")

class Candidate(db.Model, UserMixin):

    __tablename__ = 'Candidate'

    id = Column(Integer, primary_key=True)
    nomorurut = Column(Integer, unique=True, nullable=False)
    nama = Column(String, nullable=False)
    nim = Column(String, unique=True, nullable=False)
    prodi = Column(String)
    alamat = Column(String)
    angkatan = Column(Integer)
    semester = Column(Integer)
    artikel = Column(Text)
    foto = Column(String)

class Rekapitulasi(db.Model, UserMixin):

    __tablename__ = 'Rekapitulasi'

    id = Column(Integer, primary_key=True)
    id_user = Column(Integer, unique=True, nullable=False)
    token = Column(String, nullable=False)
    nomorurut = Column(Integer, nullable=False)
    waktu = Column(String, nullable=False)

    def __repr__(self):
        return str(f"Rekapitulasi(id={self.id},id_user={self.id_user},token={self.token},nomorurut={self.nomorurut},waktu={self.waktu})")

class TimeRekam(db.Model, UserMixin):

    __tablename__ = 'TimeRekam'

    id = Column(Integer, primary_key=True)
    prodi = Column(String)
    angkatan = Column(Integer)
    semester = Column(Integer)
    waktuvote = Column(String)
    abaikan = Column(Integer)

    def __repr__(self):
        return str(f"TimeRekam(waktuvote={self.waktuvote},abaikan={self.abaikan})")

@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
