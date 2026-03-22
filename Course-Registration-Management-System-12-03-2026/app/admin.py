from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection

admin = Admin(app=app, name="Course Registration Administration")


admin.add_view(ModelView(Course, db.session))
admin.add_view(ModelView(ClassSection, db.session))