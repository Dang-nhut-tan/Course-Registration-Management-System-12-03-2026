"""Admin views for base."""

from flask import flash, redirect, request, url_for
from flask_login import current_user
from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import IntegrityError

from app import db
from app.api import create_record, delete_record, update_record
from app.model import UserRole


class AdminAccessIndexView (AdminIndexView):
    def is_visible(self):
        return False

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class BaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            self.session.flush()
            delete_record(model, self.session)
            self.after_model_delete(model)
            return True
        except IntegrityError:
            db.session.rollback()
            flash("Không thể xóa dữ liệu này vì đang được sử dụng ở bảng khác.", "error")
            return False
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi hệ thống khi xóa dữ liệu: {str(e)}", "error")
            return False

    def create_model(self, form):
        try:
            model = self.build_new_instance()
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            create_record(model, self.session)
            self.after_model_change(form, model, True)
            return model
        except Exception as e:
            self.session.rollback()
            flash(f"Không thể tạo dữ liệu qua API: {str(e)}", "error")
            return False

    def update_model(self, form, model):
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            update_record(model, self.session)
            self.after_model_change(form, model, False)
            return True
        except Exception as e:
            self.session.rollback()
            flash(f"Không thể cập nhật dữ liệu qua API: {str(e)}", "error")
            return False
