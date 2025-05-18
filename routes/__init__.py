def init_app(app):
    from routes.auth import auth
    from routes.user import user
    from routes.counselor import counselor
    from routes.admin import admin
    
    app.register_blueprint(auth)
    app.register_blueprint(user)
    app.register_blueprint(counselor)
    app.register_blueprint(admin)