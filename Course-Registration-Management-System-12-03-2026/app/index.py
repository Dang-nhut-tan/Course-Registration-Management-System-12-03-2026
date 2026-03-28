from flask import redirect, render_template, request, url_for
from app import app
from app import utils
from app.model import ClassSection, Student,Course


@app.route("/",methods=['get','post'])
def login():
    err_msg=''
    if request.method.__eq__('POST'):
        student_code=request.form.get('student_code')
        password=request.form.get('password')
        user=utils.check_login_student(student_code=student_code,password=password)
        if user:
            return redirect(url_for('index'))
        else:
            return 'MSSV hoặc mật khẩu không chính xác'
    return render_template("login.html",err_msg=err_msg)

@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

@app.route("/index")
def index():
    course_id = request.args.get("course")
    faculty_id = request.args.get("faculty")
    classes=request.args.get("class")

    sections =utils.get_sections(course_id, faculty_id)
    filters = utils.get_filter_data()
    return render_template(
        "index.html",
        sections=sections,
        courses=filters["courses"],
        faculties=filters["faculties"]
    )

if __name__ == "__main__":
    app.run(debug=True)
