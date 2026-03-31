from flask_admin._types import T_SQLALCHEMY_MODEL
from flask import flash
from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.model import Course, ClassSection, Enrollment

admin = Admin(app=app, name="Course Registration Administration")

class ClassSectionView(ModelView):
    def delete_model(self, model):
        has_enrollment = db.session.query(Enrollment).filter_by(class_section_id = model.id).count() > 0

        if has_enrollment:
            flash("Không thể xóa lớp học này vì đã có sinh viên đăng ký!", "error")
            return False

        return  super(ClassSectionView, self).delete_model(model)

admin.add_view(ModelView(Course, db.session))
admin.add_view(ClassSectionView(ClassSection, db.session))