# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
Copyright (c) 2021 - Semara (semarainc)
"""
import imghdr
import json
import pandas as pd
import xlsxwriter
import os
import random
import io
import string
from flask import jsonify, render_template, redirect, request, url_for, flash, send_file, abort, current_app, make_response
from flask_caching import Cache
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app import db, login_manager
from app.base import blueprint
from app.home import blueprint as bp
from app.home.routes import admin_required
from app.base.forms import LoginForm, CreateAccountForm, CreateVoterForm, EditVoterForm, CreateCandidateForm, EditCandidateForm, TimerRekapForm
from app.base.models import User, Voter, Candidate, Rekapitulasi, TimeRekam

from app.base.util import hash_pass
from app.base.util import verify_pass
from werkzeug.utils import secure_filename

from sqlalchemy import func

from datetime import datetime

from functools import wraps

cache = Cache(config={'CACHE_TYPE': 'simple'})

def Load_Data(file_name):
    a = pd.read_csv(file_name, quotechar='"', skipinitialspace=True)

    for i, row in a.iterrows():
        print(i, row["PASSWORD"])
        if str(row["USERNAME"]).lower() == "{{random}}":
            username_ = "VTR" + id_generator(size=5) + "CLMRY"
            a.at[i,'USERNAME'] = str(username_)
        
        if str(row["PASSWORD"]).lower() == "{{random}}":
            password_ = "P" + str(id_generator(size=5)).lower() + "C"
            a.at[i,'PASSWORD'] = str(password_).lower()
        

    a.to_csv(file_name, index=False)
    list_of_rows = [list(row) for row in a.values]
    return list_of_rows

def time_perlu(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        print(current_user.username)
        voter = Voter.query.filter_by(username=current_user.username).first()
        #print(voter)
        if voter:
            print("Print")
            rekap = TimeRekam.query.filter_by(prodi=voter.prodi, angkatan=voter.angkatan, semester=voter.semester).first()
            print(rekap)
        
        if rekap:
            now = datetime.now()
            parsed_ = parse_reservasi(rekap.waktuvote)
            if rekap.abaikan == 0 and parsed_ is not None:
                VoteStats = Rekapitulasi.query.filter_by(id_user=current_user.id)
                status = {}
                if int(VoteStats.count()) > 0:
                    return f(*args, **kwargs)

                if now > parsed_[0] and now < parsed_[1]:
                    return f(*args, **kwargs)
                
                else:
                    flash("Waktu Voting Sudah Selesai atau Belum Tersedia.", 'error')
                    if current_user.is_authenticated:
                        #pass
                        logout_user()
                    return redirect(url_for('base_blueprint.login')) #This Will Be Change To Warning Vote
            
            elif rekap.abaikan == 1:
                return f(*args, **kwargs)
        
        elif rekap is None:
            VoteStats = Rekapitulasi.query.filter_by(id_user=current_user.id)
            status = {}
            if int(VoteStats.count()) > 0:
                return f(*args, **kwargs)

            logout_user()
            flash("Waktu Voting Sudah Selesai atau Belum Tersedia.", 'error')
            return redirect(url_for('base_blueprint.login'))

        return f(*args, **kwargs)
    return wrap

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0) 
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def parse_reservasi(jadwal):
    try:
        AM = [0,1,2,3,4,5,6,7,8,9,10,11]
        PM = [12,13,14,15,16,17,18,19,20,21,22,23]
        reservasi = jadwal.split(' ')
        tglawal = reservasi[0].split('/') #it will be (month,date,year)
        tglakhir = reservasi[4].split('/') #it will be (month,date,year)
        waktuawal = reservasi[1].split(":") #Hour:Minute
        waktuakhir = reservasi[5].split(":")

        if reservasi[2] == "AM":
            if waktuawal[0] == "12":
                waktuawal[0] = "0"
        elif reservasi[2] == "PM":
            if waktuawal[0] != "12":
                waktuawal[0] = PM[AM.index(int(waktuawal[0]))]
        
        if reservasi[6] == "AM":
            if waktuakhir[0] == "12":
                waktuakhir[0] = "0"
        elif reservasi[6] == "PM":
            if waktuakhir[0] != "12":
                waktuakhir[0] = PM[AM.index(int(waktuakhir[0]))]
        
        tAwal = datetime(year=int(tglawal[2]), month=int(tglawal[0]), 
                        day=int(tglawal[1]), hour=int(waktuawal[0]), minute=int(waktuawal[1]))

        tAkhir = datetime(year=int(tglakhir[2]), month=int(tglakhir[0]), 
                        day=int(tglakhir[1]), hour=int(waktuakhir[0]), minute=int(waktuakhir[1]))
        
        
        return (tAwal, tAkhir)
    except:
        return None

@blueprint.route('/')
def route_default():
    try:
        if current_user.role == 'admin':
            return redirect(url_for('base_blueprint.dashboard'))
        elif current_user.role == "voter":
            return redirect(url_for('base_blueprint.Vdash'))
        elif current_user.role == "pdd":
            return redirect(url_for('base_blueprint.indexPDD'))
    except:
        pass

    return redirect(url_for('home_blueprint.index'))

@cache.cached(timeout=60)
@blueprint.route('/cdatavote')
def CDataVote():
    # Buat dinamis untuk semua kandidat
    HakSuara = db.session.query(func.count(Rekapitulasi.id)).scalar()
    Pemilihs = db.session.query(func.count(Voter.id)).scalar()

    # Ambil semua kandidat
    kandidat_list = Candidate.query.order_by(Candidate.nomorurut).all()
    data = []
    for kandidat in kandidat_list:
        jumlah_suara = int(Rekapitulasi.query.filter_by(nomorurut=kandidat.nomorurut).count())
        data.append({"name": kandidat.nama, "data": [jumlah_suara]})
    # Tambahkan info summary
    data.append({"HakSuara": HakSuara, "Pemilih": Pemilihs, "Kandidat": len(kandidat_list)})
    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return response

@blueprint.route('/indexPDD')
@login_required
def indexPDD():
    if current_user.role == 'pdd':
        status = {}
        HakSuara = db.session.query(func.count(Rekapitulasi.id)).scalar()
        Pemilihs = db.session.query(func.count(Voter.id)).scalar()

        status["HakSuara"] = str(HakSuara)
        status["Pemilih"] = str(Pemilihs)
        status["Calon"] = 2
        return render_template( 'pddIndex.html', status=status)
    else:
        return redirect(url_for('base_blueprint.route_default'))

@blueprint.route('/dashboard')
@login_required
@admin_required
def dashboard():
    status = {}
    VoteStats = TimeRekam.query.first()
    Calon = Candidate.query.all()
    HakSuara = db.session.query(func.count(Rekapitulasi.id)).scalar()
    Pemilihs = db.session.query(func.count(Voter.id)).scalar()
    Sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    status["Kandidats"] = []
    status["SuaraGet"] = []
    for i in Calon:
        status["SuaraGet"].append(Rekapitulasi.query.filter_by(nomorurut=i.nomorurut).count())
        status["Kandidats"].append(str(i.nama))
    
    if len(status["Kandidats"]) < 1:
        status["Kandidats"].append("DummyNobody")
    if len(status["SuaraGet"]) < 1:
        status["SuaraGet"].append(0)

    if VoteStats:
        isVoteOpen = int(VoteStats.abaikan)
        parsed2_ = parse_reservasi(VoteStats.waktuvote)
        if isVoteOpen == 0:
            if now > parsed2_[0] and now < parsed2_[1]:
                status["StatusVote"] = "Feature Disabled"#"Terbuka Terjadwal"
            else:
                status["StatusVote"] = "Feature Disabled"#"Tertutup"
        elif isVoteOpen == 1:
            status["StatusVote"] = "Feature Disabled"#"Terbuka Permanen"
        else:
            status["StatusVote"] = "Feature Disabled"#"Tertutup"
    else:
        status["StatusVote"] = "Fail To Retrive"
    status["HakSuara"] = str(HakSuara)
    status["Pemilih"] = str(Pemilihs)
    status["sekarang"] = Sekarang
    status["Calon"] = Calon
    return render_template( 'index2.html', status=status)
## Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    print(request.form)
    login_form = LoginForm(request.form)
    if 'login' in request.form:
        print("Login Readines")
        # read form data
        username = str(request.form['username']).lower()
        password = request.form['password']
        remember = request.form.get("remember", None)

        if request.form.get("login") == 'login_panitia':
            tipe="panitia"
        else:
            tipe="pemilih"

        # Locate user using normal username
        user = User.query.filter_by(username=username).first()
        
        # Check the password
        if user and verify_pass( password, user.password):

            if tipe == 'pemilih' and (user.role == 'admin' or user.role == 'pdd'):
                return render_template( 'accounts/login2.html', msg='Wrong user or password', tipe=tipe, form=login_form)
            elif tipe == 'panitia' and user.role == "voter":
                return render_template( 'accounts/login2.html', msg='Wrong user or password', tipe=tipe, form=login_form)
    
            if remember is not None:
                login_user(user, remember=True)
            else:
                login_user(user)

            return redirect(url_for('base_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template( 'accounts/login2.html', msg='Wrong user or password', tipe=tipe, form=login_form)

    if not current_user.is_authenticated:
        return render_template( 'accounts/login2.html',
                                form=login_form, tipe=None)
    return redirect(url_for('base_blueprint.route_default'))

@blueprint.route('/register_nulled', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username  = request.form['username']
        email     = request.form['email'   ]

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template( 'accounts/register.html', 
                                    msg='Username already registered',
                                    success=False,
                                    form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template( 'accounts/register.html', 
                                    msg='Email already registered', 
                                    success=False,
                                    form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        user.roles = "pdd"
        #print(user)
        db.session.add(user)
        db.session.commit()

        return render_template( 'accounts/register.html', 
                                msg='User created please <a href="/login">login</a>', 
                                success=True,
                                form=create_account_form)

    else:
        return render_template( 'accounts/register.html', form=create_account_form)

@blueprint.route('/viewvoters', methods=['GET'])
@login_required
@admin_required
def voterlist():
    voter = Voter.query.all() #tuple
    #print(voter)
    milihList = []
    for i in voter:
        #print(i)
        UserID = User.query.filter_by(username=i.username).first()
        print(UserID)
        i.password2 = UserID.password2
        statsSuara = Rekapitulasi.query.filter_by(id_user=UserID.id).count()
        print(statsSuara)
        if statsSuara > 0:
            milihList.append(int(i.id))
            if i.id in milihList:
                print("True")
    return render_template( 'admin/tables-data.html', voters=voter, milih=milihList)

@blueprint.route('/deletevoter', methods=['GET', 'POST'], defaults={'user_id': None})
@blueprint.route('/deletevoter/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def deletevoter(user_id):
    if user_id is None:
        return redirect(url_for('base_blueprint.voterlist'))

    voter = Voter.query.filter_by(id=user_id).first()
    user = User.query.filter_by(username=voter.username).first()
    db.session.delete(voter)
    db.session.delete(user)
    db.session.commit()

    flash("Voter Deleted Successfully")
    return redirect(url_for('base_blueprint.voterlist'))

@blueprint.route('/uploadvoter', methods=['GET', 'POST'], defaults={'status': None})
@blueprint.route('/uploadvoter/<int:status>', methods=['GET', 'POST'])
@login_required
@admin_required
def uploadvoter(status):

    print(current_app.root_path)
    basedir    = os.path.abspath(os.path.dirname(__file__))
    UPLOADED_IMAGES_DEST = os.path.join(current_app.root_path , "base/static/assets/voter")
    UPLOAD_EXTENSIONS = ['.csv']

    if request.method == "GET" and status == 1:
        try:
            file_name = os.path.join(UPLOADED_IMAGES_DEST, "daftarnamavoter.csv")
            data = Load_Data(file_name) 

            for i in data:

                isUser = User.query.filter_by(username=str(i[7]).lower()).first()
                if isUser:
                    Voter_ =  Voter.query.filter_by(username=isUser.username).first()
                else:
                    Voter_ = None
                if not isUser:
                    user_Voter = User(username=str(i[7]).lower(), password=i[8], email=i[6], role="voter")
                    voter_identity = Voter(username=str(i[7]).lower(), email=i[6], nim=i[0],
                                    nama=i[1], prodi=i[2], alamat=i[3], angkatan=i[4], semester=i[5])
                    db.session.add(user_Voter) #Add all the records
                    db.session.add(voter_identity)
                elif isUser:
                    Voter_.username = i[7]
                    Voter_.nama = i[1]
                    Voter_.alamat = i[3]
                    Voter_.angkatan = i[4]
                    Voter_.semester = i[5]
                    Voter_.email = i[6]
                    Voter_.prodi = i[2]
                    isUser.email = i[6]
                    isUser.username = str(i[7]).lower()
                    isUser.password = b'' + hash_pass(i[8])
                    isUser.password2 = i[8]

            db.session.commit() #Attempt to commit all the records

            if os.path.isfile(os.path.join(UPLOADED_IMAGES_DEST, "daftarnamavoter.csv")):
                os.remove(os.path.join(UPLOADED_IMAGES_DEST, "daftarnamavoter.csv"))
            flash("Success Proceed CSV")
            return redirect(url_for('base_blueprint.uploadvoter'))
        except Exception as e:
            print(e)
            db.session.rollback() #Rollback the changes on error
            if os.path.isfile(os.path.join(basedir, UPLOADED_IMAGES_DEST, "daftarnamavoter.csv")):
                os.remove(os.path.join(basedir, UPLOADED_IMAGES_DEST, "daftarnamavoter.csv"))
            flash(f"[{str(e)}]Fail To Proceed CSV, Check For Duplicate Data")
            return redirect(url_for('base_blueprint.uploadvoter'))

    if request.method == "GET" and status is None:
        return render_template("admin/tables-csv.html", candidates_=None)
    
    if request.method == "POST":
        if status is None:
            csv_file = request.files["csvfile"]

            #Handle Image Upload (Not Yet)

            filename = secure_filename(csv_file.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                print(file_ext)
                if file_ext not in UPLOAD_EXTENSIONS:
                    return render_template( 'admin/tables-csv.html', msg="Format CSV Tidak Valid",success=False, candidates_=None)
                namafiles = "daftarnamavoter.csv"

                csv_file.save(os.path.join(UPLOADED_IMAGES_DEST, namafiles))
                
                #Load it then render to html
                data = Load_Data(os.path.join(UPLOADED_IMAGES_DEST, namafiles)) 
                return render_template( 'admin/tables-csv.html', msg="Silahkan Cek Sebelum Validasi",success=False, candidates_=data)

@blueprint.route('/addvoter', methods=['GET', 'POST'])
@login_required
@admin_required
def addvoter():
    create_account_form = CreateVoterForm(request.form)
    if 'addvoter' in request.form:
        print("Addvoter Running")
        nama      = request.form['nama']
        nim       = request.form['nim']
        alamat    = request.form['alamat']
        angkatan  = request.form['angkatan']
        semester  = request.form['semester']
        prodi     = request.form['prodi']
        username  = request.form['username']
        email     = request.form['email'   ]

        # Check usename exists
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template( 'admin/examples-add.html', 
                                    msg='Username already registered',
                                    success=False,
                                    form=create_account_form)
        
        # Check nim exists
        voter = Voter.query.filter_by(nim=nim).first()
        if voter:
            return render_template( 'admin/examples-add.html', 
                                    msg='Nim already registered',
                                    success=False,
                                    form=create_account_form)

        # Check email exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template( 'admin/examples-add.html', 
                                    msg='Email already registered', 
                                    success=False,
                                    form=create_account_form)

        # else we can create the user
        user = User(username=username, email=email, password=request.form['password'])
        voter = Voter(username=username, nama=nama, nim=nim, alamat=alamat, angkatan=angkatan, semester=semester, email=email, prodi=prodi)
        #print(user)
        #print(voter)
        db.session.add(user)
        db.session.add(voter)
        db.session.commit()
        print("Succkeess")
        flash("Voter Created Successfully")
        return redirect(url_for('base_blueprint.addvoter'))

        #return render_template( 'admin/examples-add.html', 
        #                        msg='Voter created please <a href="/login">login</a>', 
        #                        success=True,
        #                        form=create_account_form)

    else:
        return render_template( 'admin/examples-add.html', form=create_account_form)

@blueprint.route('/editvoter', methods=['GET', 'POST'], defaults={'user_id': None})
@blueprint.route('/editvoter/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editvoter(user_id):

    if user_id is not None and 'editvoter' not in request.form:
        voter = Voter.query.filter_by(id=user_id).first()
        user = User.query.filter_by(username=voter.username).first()

        try:
            a = user.username
        except:
            flash("Data Not Found")
            return redirect(url_for('base_blueprint.addvoter'))

        edit_account_form = EditVoterForm(id=user_id, nama=voter.nama, 
                                        nim=voter.nim, alamat=voter.alamat,
                                        angkatan=voter.angkatan, semester=voter.semester,
                                        prodi=voter.prodi,
                                        username=user.username, email=user.email)

        return render_template( 'admin/examples-edit.html', form=edit_account_form)
    
    if 'editvoter' in request.form:
        edit_account_form = EditVoterForm(request.form)

        print(request.form)
        id        = request.form["id"]
        nama      = request.form['nama']
        nim       = request.form['nim']
        alamat    = request.form['alamat']
        angkatan  = request.form['angkatan']
        semester  = request.form['semester']
        prodi     = request.form['prodi']
        username  = request.form['username']
        email     = request.form['email'   ]
        password  = request.form.get('password', None)

        # Check password exists
        voter = Voter.query.filter_by(id=id).first()
        user = User.query.filter_by(username=voter.username).first()
        if (password is None) or password == "":
            voter.username = username
            voter.nama = nama
            voter.nim = nim
            voter.alamat = alamat
            voter.angkatan = angkatan
            voter.semester = semester
            voter.email = email
            voter.prodi = prodi
            user.email = email
            user.username = username
        else:
            voter.username = username
            voter.nama = nama
            voter.alamat = alamat
            voter.angkatan = angkatan
            voter.semester = semester
            voter.email = email
            voter.prodi = prodi
            user.email = email
            user.username = username
            user.password = b'' + hash_pass(password)
            user.password2 = password
        
        print("UPDATE DATA")
        #db.session.query(user).update()
        #db.session.query(voter).update()
        db.session.commit()

        flash("Voter Edited Successfully")
        return redirect(url_for('base_blueprint.voterlist'))

    else:
        return redirect(url_for('base_blueprint.voterlist')) #Will Change To List Voter

#------------USERLAND------------------
"""
    Let me give little Explanation, im doing this because im run out of time T_T, 
    so better merge between server and userland :)
    i hope you can understand this, also
    i hope i could fix this matter in the future :D
"""

@blueprint.route('/printbukti', methods=['GET', 'POST'])
@login_required
def printbukti():

    # Not Finished
    VoteStats = Rekapitulasi.query.filter_by(id_user=current_user.id)
    status = {}
    if int(VoteStats.count()) > 0:
        status["pesan"] = "Terima Kasih Karena Anda Sudah Melakukan Voting"
        status["Token"] = str(VoteStats.first().token)
        status["waktuvote"] = str(VoteStats.first().waktu)
        tmp = User.query.filter_by(id=current_user.id).first()
        print(tmp)
        status["voter"] = Voter.query.filter_by(username=tmp.username).first()
        print(status["voter"])
        return render_template('print_nota.html', status=status)

@blueprint.route('/voters/votethis', methods=['GET', 'POST'])
@login_required
@time_perlu
def votethis():

    # Not Finished
    VoteStats = Rekapitulasi.query.filter_by(id_user=current_user.id)
    status = {}
    if int(VoteStats.count()) > 0:
        status["pesan"] = "Terima Kasih Karena Anda Sudah Melakukan Voting"
        status["Token"] = str(VoteStats.first().token)
        status["waktuvote"] = str(VoteStats.first().waktu)
        tmp = User.query.filter_by(id=current_user.id).first()
        print(tmp)
        status["voter"] = Voter.query.filter_by(username=tmp.username).first()
        print(status["voter"])
        return render_template('daftar_kandidat.html', status=status)
    
    if request.method == 'POST':
        print(request.form)
        nomorurut = request.form["calon"]
        id_user = current_user.id
        print("ID USER")
        print(id_user)
        waktu = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        token2 = id_generator()

        rekap = Rekapitulasi(nomorurut=nomorurut, id_user=id_user, waktu=waktu, token=token2)
        db.session.add(rekap)
        db.session.commit()
        return redirect(url_for('base_blueprint.votethis'))

    if request.method == 'GET':
        status["pesan"] = ""
        kandidat = Candidate.query.order_by(Candidate.nomorurut).all()
        status["kandidat"] = kandidat
        status["voter"] = None
        return render_template('daftar_kandidat.html', status=status)

@blueprint.route('/voters/profilcalon', methods=['GET'], defaults={'calon_id': None})
@blueprint.route('/voters/profilcalon/<int:calon_id>', methods=['GET'])
@login_required
@time_perlu
def profilcalon(calon_id):
    if calon_id is None:
        return redirect(url_for('base_blueprint.votethis'))
    
    calons = Candidate.query.filter_by(id=calon_id).first()
    print(calons)
    return render_template("profil_kandidat.html", calons=calons)

@cache.cached(timeout=50)
@blueprint.route('/voters/ceksuara', methods=['GET'], defaults={'token': None})
@blueprint.route('/voters/ceksuara/<string:token>', methods=['GET'])
def ceksuara(token):
    if token is None or token == "":
        return render_template("ceksuara.html", token=None)
    
    token = Rekapitulasi.query.filter_by(token=token).first()

    return render_template("ceksuara.html", token=token)

@cache.cached(timeout=50)
@blueprint.route('/voters/dashboard', methods=['GET'])
@login_required
@time_perlu
def Vdash():
    userss_ = User.query.filter_by(id=current_user.id).first()
    calons = Voter.query.filter_by(username=userss_.username).first()
    print(calons)
    print(current_user.id)
    if calons:
        return render_template("profil_user.html", calons=calons)

    return redirect(url_for('base_blueprint.votethis'))
    
    

#-----------Rekapitulasi----------
@blueprint.route('/printrekap', methods=['GET'], defaults={'tipe': None})
@blueprint.route('/printrekap/<string:tipe>', methods=['GET'])
@login_required
@admin_required
def printrekap(tipe):

    if tipe is None:
        flash("Print Data Invalid")
        return redirect(url_for('base_blueprint.rekapitulasi'))

    if tipe in ['suara', 'pemilih']:
        if tipe == 'suara':
            rekap = Rekapitulasi.query.all()
            proxy = io.BytesIO()
    
            workbook = xlsxwriter.Workbook(proxy, {'in_memory': True})
            worksheet1 = workbook.add_worksheet()

            bold = workbook.add_format({'bold': 1})

            # Make the columns wider.
            worksheet1.set_column('A:E', 14)
            # Make the header row larger.
            worksheet1.set_row(0, 20, bold)

            worksheet1.write_row('A1', ['ID', 'JURUSAN', 'TOKEN', 'NOMOR URUT', 'WAKTU'])


            #For Some Line Need To Be Empty i guess??
            #This List Will Be Static Unfortunately -,-
            listKandidat = {"1": "Ruby Firdaus", '2': "Zahrowi Adib"}
            rekap1 = int(Rekapitulasi.query.filter_by(nomorurut=1).count())
            rekap2 = int(Rekapitulasi.query.filter_by(nomorurut=2).count())
            jmlPemilih = int(Voter.query.count())
            print(rekap1, rekap2)

            # Set the autofilter.
            worksheet1.autofilter(f'A1:E{rekap1+rekap2}')

            row = 1
            for i in rekap:
                users = User.query.filter_by(id=i.id_user).first()
                jurusan = Voter.query.filter_by(username=users.username).first()
                worksheet1.write_row(row, 0, ['REKAP-%04d' % i.id, jurusan.prodi, i.token, i.nomorurut, i.waktu])
                row += 1

            data_format2 = workbook.add_format({'bg_color': '#00C7CE'})
            data_format3 = workbook.add_format({'bg_color': '#B1C7C0'})
            data_format4 = workbook.add_format({'bg_color': '#00C6CE'})
            worksheet1.write_row(row+2, 0, [f'Total Suara {listKandidat["1"]}:', f'{rekap1} Suara'], cell_format=data_format2)
            worksheet1.write_row(row+3, 0, [f'Total Suara {listKandidat["2"]}:', f'{rekap2} Suara'], cell_format=data_format3)
            worksheet1.write_row(row+4, 0, [f'Total Suara:', f'{rekap1+rekap2} Suara'], cell_format=data_format3)
            worksheet1.write_row(row+5, 0, [f'Total Pemilih Terdaftar:', f'{jmlPemilih} Pemilih'], cell_format=data_format4)

            workbook.close()
            # Creating the byteIO object from the StringIO Object
            mem = io.BytesIO()
            mem.write(proxy.getvalue())
            # seeking was necessary. Python 3.5.2, Flask 0.12.2
            mem.seek(0)
            proxy.close()

            flash("Print File Rekapan Suara Berhasil")
            return send_file(
                mem,
                as_attachment=True,
                download_name='rekapan_suara.xlsx',
                mimetype='text/csv'
            )
        elif tipe == 'pemilih':
            rekap = Voter.query
            proxy = io.BytesIO()

            workbook = xlsxwriter.Workbook(proxy, {'in_memory': True})
            worksheet1 = workbook.add_worksheet()

            bold = workbook.add_format({'bold': 1})

            # Make the columns wider.
            worksheet1.set_column('A:K', 17)
            # Make the header row larger.
            worksheet1.set_row(0, 20, bold)

            worksheet1.write_row('A1', ['ID', 'USERNAME', 'PASSWORD', 'NAMA', 'NIM', 'PROGRAM STUDI', 'ANGKATAN', 'SEMESTER', 'EMAIL', 'ALAMAT', "STATUS"])
            
            # Set the autofilter.
            worksheet1.autofilter(f'A1:K{rekap.count()}')

            row = 1
            for i in rekap.all():
                UserID = User.query.filter_by(username=i.username).first()
                i.password2 = UserID.password2
                print(UserID)
                statsSuara = Rekapitulasi.query.filter_by(id_user=UserID.id).count()
                if statsSuara > 0:
                    isMilih = "SUDAH MEMILIH"
                else:
                    isMilih = "BELUM MEMILIH"
                id_pemilih = 'VOTERS-%04d' % i.id
                worksheet1.write_row(row, 0, [id_pemilih, i.username, i.password2, i.nama, i.nim, i.prodi, i.angkatan, i.semester, i.email, i.alamat, isMilih])
                row += 1
            
            data_format2 = workbook.add_format({'bg_color': '#00C7CE'})

            worksheet1.write_row(row+2, 0, [f'Total Pemilih:', f'{rekap.count()} Pemilih'], cell_format=data_format2)

            workbook.close()

            # Creating the byteIO object from the StringIO Object
            mem = io.BytesIO()
            mem.write(proxy.getvalue())
            # seeking was necessary. Python 3.5.2, Flask 0.12.2
            mem.seek(0)
            proxy.close()

            flash("Print File Rekapan Pemilih Berhasil")
            return send_file(
                mem,
                as_attachment=True,
                download_name='rekapan_pemilih.xlsx',
                mimetype='text/csv'
            )
    return redirect(url_for('base_blueprint.rekapitulasi'))

@blueprint.route('/rekapitulasi', methods=['GET'])
@login_required
@admin_required
def rekapitulasi():
    rekap = Rekapitulasi.query.all()
    for i in rekap:
        user = User.query.filter_by(id=i.id_user).first()
        jurusan = Voter.query.filter_by(username=user.username).first().prodi
        i.jurusan = jurusan
    return render_template( 'admin/tables-suara.html', candidates_=rekap)

@blueprint.route('/removevote', methods=['POST'])
@login_required
@admin_required
def removevote():
    Rekapitulasi.query.delete()
    db.session.commit()
    flash("Record Sudah Dihapus")
    return redirect(url_for('base_blueprint.rekapitulasi'))

@blueprint.route('/rekaptimer', methods=['GET'])
@login_required
@admin_required
def rekaptimer():
    rekap = TimeRekam.query.all()
    return render_template( 'admin/tables-timer.html', candidates_=rekap)

@blueprint.route('/removerekaptimer', methods=['GET', 'POST'], defaults={'id_time': None})
@blueprint.route('/removerekaptimer/<int:id_time>', methods=['GET', 'POST'])
@login_required
@admin_required
def removerekaptimer(id_time):
    if id_time is None:
        return redirect(url_for('base_blueprint.rekaptimer'))

    rekap = TimeRekam.query.filter_by(id=id_time).first()

    db.session.delete(rekap)
    db.session.commit()

    flash("Jadwal Voting Deleted Successfully")
    return redirect(url_for('base_blueprint.rekaptimer'))
    

@blueprint.route('/addrekaptimer', methods=['GET', 'POST'])
@login_required
@admin_required
def addrekaptimer():

    rekap_form = TimerRekapForm()
    if request.method == "GET":
        return render_template( 'admin/rekaptimer.html', form=rekap_form, rekap=None)

    elif request.method == "POST":
        print(request.form)
        prodi = request.form.get('prodi', None)
        angkatan = request.form.get('angkatan', None)
        semester = request.form.get('semester', None)
        reservasi = request.form.get('reservasi', None)
        abaikan = request.form.get('abaikan', None)

        #abaikan status code
        #0 = correlate with time
        #1 = abandon time, stays open vote
        #2 = close vote by force (if record doesnt exists then vote is closed)

        if prodi is None or angkatan is None or semester is None:
            return render_template( 'admin/rekaptimer.html', msg="Ada Field Yang Kosong",success=False, rekap=None, form=rekap_form)
            
        if reservasi is not None:
            rekap = TimeRekam.query.filter_by(prodi=prodi, angkatan=angkatan, semester=semester).first()
            if rekap:
                return render_template( 'admin/rekaptimer.html', msg="Data Jadwal Sudah Ada, Silahkan Diedit",success=False, rekap=rekap, form=rekap_form)
            else:
                Rekaman = TimeRekam(prodi=prodi, angkatan=angkatan, semester=semester, waktuvote=str(reservasi), abaikan=0)
                db.session.add(Rekaman)
                db.session.commit()
            flash("Jadwal Voting Sukses Ditambahkan")
            return redirect(url_for('base_blueprint.rekaptimer'))
        elif abaikan is not None:
            rekap = TimeRekam.query.filter_by(prodi=prodi, angkatan=angkatan, semester=semester).first()
            if rekap:
                return render_template( 'admin/rekaptimer.html', msg="Data Jadwal Sudah Ada, Silahkan Diedit",success=False, rekap=rekap, form=rekap_form)
            else:
                Rekaman = TimeRekam(prodi=prodi, angkatan=angkatan, semester=semester, waktuvote="", abaikan=1)
                db.session.add(Rekaman)
                db.session.commit()
            flash("Jadwal Voting Sukses Ditambahkan")
            return redirect(url_for('base_blueprint.rekaptimer')) 
        else:
            return render_template( 'admin/rekaptimer.html', msg="Sended Data is Invalid",success=False, rekap=None)

#----------CANDIDATE--------------
@cache.cached(timeout=50)
@blueprint.route('/quickcount', methods=['GET'])
def quickcount():
    kandidate = Candidate.query.order_by(Candidate.nomorurut).all()
    suara = {}
    for i in kandidate:
        suara[i.nomorurut] = Rekapitulasi.query.filter_by(nomorurut=i.nomorurut).count()
    return render_template( 'quick.html', candidates_=kandidate, suara=suara)

@blueprint.route('/viewcandidate', methods=['GET', 'POST'])
@login_required
@admin_required
def candidatelist():
    kandidate = Candidate.query.all()
    return render_template( 'admin/tables-candidate.html', candidates_=kandidate)

@blueprint.route('/addcandidate', methods=['GET', 'POST'])
@login_required
@admin_required
def addcandidate():
    create_account_form = CreateCandidateForm(request.form)
    if 'addcandidate' in request.form:
        print("Addcandidate Running")

        nomorurut = request.form['nomorurut']
        nama      = request.form['nama']
        nim       = request.form['nim']
        alamat    = request.form['alamat']
        angkatan  = request.form['angkatan']
        semester  = request.form['semester']
        prodi     = request.form['prodi']
        artikel   = request.form['artikel']
        foto      = request.files['foto']

        if int(nomorurut) < 1:
            return render_template( 'admin/kandidat-add.html', 
                                    msg='Nomor Urut Tidak Valid',
                                    success=False,
                                    form=create_account_form)
        # Check nomorurut exists
        kandidate = Candidate.query.filter_by(nomorurut=nomorurut).first()
        if kandidate:
            return render_template( 'admin/kandidat-add.html', 
                                    msg='Nomor Urut already registered',
                                    success=False,
                                    form=create_account_form)
        
        # Check nim exists
        kandidate = Candidate.query.filter_by(nim=nim).first()
        if kandidate:
            return render_template( 'admin/kandidat-add.html', 
                                    msg='Nim already registered',
                                    success=False,
                                    form=create_account_form)

        #Handle Image Upload (Not Yet)
        UPLOADED_IMAGES_DEST = os.path.join(current_app.root_path, "base/static/assets/kandidat")
        UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif', '.jpeg']

        filename = secure_filename(foto.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            print(file_ext)
            if file_ext not in UPLOAD_EXTENSIONS or \
                    file_ext != validate_image(foto.stream):
                return render_template( 'admin/kandidat-add.html', msg="Format Gambar Tidak Valid",success=False, form=create_account_form)
            namafiles = ''.join(random.choice(string.ascii_lowercase) for i in range(16)) + str(file_ext)

        # else we can create the user
        kandidate = Candidate(nomorurut=nomorurut,nama=nama, nim=nim, alamat=alamat, angkatan=angkatan, semester=semester, prodi=prodi,artikel=artikel, foto=namafiles)

        db.session.add(kandidate)
        db.session.commit()

        basedir    = os.path.abspath(os.path.dirname(__file__))
        foto.save(os.path.join(UPLOADED_IMAGES_DEST, namafiles))
        print("Succkeess")
        flash("Candidate Created Successfully")
        return redirect(url_for('base_blueprint.candidatelist')) #Soon Will be CandidateList

        #return render_template( 'admin/examples-add.html', 
        #                        msg='Voter created please <a href="/login">login</a>', 
        #                        success=True,
        #                        form=create_account_form)

    else:
        return render_template( 'admin/kandidat-add.html', form=create_account_form)

@blueprint.route('/editcandidate', methods=['GET', 'POST'], defaults={'cand_id': None})
@blueprint.route('/editcandidate/<int:cand_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editcandidate(cand_id):

    if cand_id is not None and 'editcandidate' not in request.form:
        kandidate = Candidate.query.filter_by(id=cand_id).first()

        try:
            a = kandidate.nomorurut
        except:
            flash("Data Not Found")
            return redirect(url_for('base_blueprint.candidatelist')) #Soon will be candidate list

        edit_account_form = EditCandidateForm(id=kandidate.id, nomorurut=kandidate.nomorurut, nama=kandidate.nama, 
                                        nim=kandidate.nim, alamat=kandidate.alamat,
                                        angkatan=kandidate.angkatan, semester=kandidate.semester,
                                        prodi=kandidate.prodi, artikel=kandidate.artikel)

        return render_template( 'admin/kandidat-edit.html', form=edit_account_form)
    
    if 'editcandidate' in request.form:
        edit_account_form = EditCandidateForm(request.form)

        #print(request.form)
        nomorurut = request.form['nomorurut']
        nama      = request.form['nama']
        nim       = request.form['nim']
        alamat    = request.form['alamat']
        angkatan  = request.form['angkatan']
        semester  = request.form['semester']
        prodi     = request.form['prodi']
        artikel   = request.form['artikel']
        foto      = request.files['foto']

        filename = secure_filename(foto.filename)

        # Check password exists
        kandidate = Candidate.query.filter_by(id=cand_id).first()

        if filename == '':
            kandidate.nomorurut = nomorurut
            kandidate.nama = nama
            kandidate.nim = nim
            kandidate.alamat = alamat
            kandidate.angkatan = angkatan
            kandidate.semester = semester
            kandidate.prodi = prodi
            kandidate.artikel = artikel
        else:
            kandidate.nomorurut = nomorurut
            kandidate.nama = nama
            kandidate.nim = nim
            kandidate.alamat = alamat
            kandidate.angkatan = angkatan
            kandidate.semester = semester
            kandidate.prodi = prodi
            kandidate.artikel = artikel

            UPLOADED_IMAGES_DEST = os.path.join(current_app.root_path, "base/static/assets/kandidat")
            UPLOAD_EXTENSIONS = ['.jpg', '.png', '.gif']
            filename = secure_filename(foto.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in UPLOAD_EXTENSIONS or \
                        file_ext != validate_image(foto.stream):
                    abort(400)
                namafiles = str(kandidate.foto)
                basedir    = os.path.abspath(os.path.dirname(__file__))
                foto.save(os.path.join(UPLOADED_IMAGES_DEST, namafiles))
        
        print("UPDATE DATA")
        #db.session.query(user).update()
        #db.session.query(voter).update()
        db.session.commit()

        flash("Candidate Edited Successfully")
        return redirect(url_for('base_blueprint.candidatelist'))

    else:
        return redirect(url_for('base_blueprint.candidatelist')) #Will Change To List Candidate

@blueprint.route('/deletecandidate', methods=['GET', 'POST'], defaults={'cand_id': None})
@blueprint.route('/deletecandidate/<int:cand_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def deletecandidate(cand_id):
    if cand_id is None:
        return redirect(url_for('base_blueprint.candidatelist'))

    kandidate = Candidate.query.filter_by(id=cand_id).first()

    UPLOADED_IMAGES_DEST = os.path.join(current_app.root_path, "base/static/assets/kandidat")
    basedir    = os.path.abspath(os.path.dirname(__file__))
    os.remove(os.path.join(UPLOADED_IMAGES_DEST, kandidate.foto))
    db.session.delete(kandidate)
    db.session.commit()

    flash("Candidate Deleted Successfully")
    return redirect(url_for('base_blueprint.candidatelist'))

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))

## Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    flash("Login is Required")
    return redirect(url_for('base_blueprint.login'))
    #return render_template('page-403.html'), 403

@blueprint.errorhandler(403)
def access_forbidden(error):
    #flash("Login is Required")
    #return redirect(url_for('base_blueprint.login'))
    return render_template('page-403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('page-500.html'), 500
