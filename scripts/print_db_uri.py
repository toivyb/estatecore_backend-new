from estatecore_backend import create_app
app = create_app()
print(app.config["SQLALCHEMY_DATABASE_URI"])
