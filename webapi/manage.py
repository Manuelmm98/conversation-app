

def deploy():
    """ Run deployment tasks"""
    from app import db, ma, Inspections
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///newdb.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    ma.init_app(app)
    
    app.app_context().push()
    
    """ Create database and tables"""
    db.create_all()
    
deploy()
