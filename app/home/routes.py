# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
Copyright (c) 2021 - Semara (semarainc)
"""

from app.home import blueprint
from app.base import blueprint as bp
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
from functools import wraps

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        #print(current_user)
        if current_user.role == "admin":
            #print(current_user)
            return f(*args, **kwargs)
        else:
            flash("You need to be an admin to view this page.")
            return redirect(url_for('base_blueprint.login')) #This Will Be Change For Voter Index

    return wrap

@blueprint.route('/index')
def index():

    return render_template('indexnew.html')

@blueprint.route('/<template>')
@login_required
@admin_required
def route_template(template):
    try:

        if not template.endswith( '.html' ):
            template += '.html'

        # Detect the current page
        segment = get_segment( request )

        # Serve the file (if exists) from bem.app/templates/FILE.html
        return render_template( template, segment=segment )

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500

# Helper - Extract current page name from request 
def get_segment( request ): 

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment    

    except:
        return None  
