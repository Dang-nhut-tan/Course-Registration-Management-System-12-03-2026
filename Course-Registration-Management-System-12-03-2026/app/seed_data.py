import hashlib
from datetime import datetime

from app import app, db
from app.model import Campus,ClassSection,ClassSectionType,Course,CourseMajor,CoursePrerequisite,Enrollment,EnrollmentStatus,Faculty,Major,Room,Schedule,Student,StudentClass,Teacher,TrainingProgram,TrainingProgramCourse,User,UserRole


sample_data = {
    "faculties": [
        {"id": 1, "name": "CNTT"},
        {"id": 2, "name": "Kinh tế"},
        {"id": 3, "name": "Quản trị kinh doanh"},
    ],
    "majors": [
        {"id": 1, "name": "HTTQL", "faculty_id": 1},
        {"id": 2, "name": "Khoa học máy tính", "faculty_id": 1},
        {"id": 3, "name": "Tài chính - Ngân hàng", "faculty_id": 2},
        {"id": 4, "name": "Marketing", "faculty_id": 3},
    ],
    "student_classes": [
        {"id": 1, "code": "DH23IM01", "name": "Lớp DH23IM01", "school_year": "2023", "major_id": 1},
        {"id": 4, "code": "DH23IM02", "name": "Lớp DH23IM02", "school_year": "2023", "major_id": 1},
        {"id": 5, "code": "DH23CS01", "name": "Lớp DH23CS01", "school_year": "2023", "major_id": 2},
        {"id": 6, "code": "DH23CS02", "name": "Lớp DH23CS02", "school_year": "2023", "major_id": 2},
        {"id": 2, "code": "DH23TC01", "name": "Lớp DH23TC01", "school_year": "2023", "major_id": 3},
        {"id": 3, "code": "DH22MK01", "name": "Lớp DH22MK01", "school_year": "2022", "major_id": 4},
    ],
    "training_programs": [
        {"id": 1, "name": "Chương trình đào tạo HTTQL khóa 2023", "major_id": 1, "school_year": "2023", "max_credits_per_semester": 25},
        {"id": 5, "name": "Chương trình đào tạo Khoa học máy tính khóa 2023", "major_id": 2, "school_year": "2023", "max_credits_per_semester": 25},
        {"id": 2, "name": "Chương trình đào tạo Tài chính - Ngân hàng khóa 2023", "major_id": 3, "school_year": "2023", "max_credits_per_semester": 25},
        {"id": 3, "name": "Chương trình đào tạo Marketing khóa 2022", "major_id": 4, "school_year": "2022", "max_credits_per_semester": 25},
    ],
    "students": [
        {"student_code": "2354050113", "name": "Nguyễn Văn A", "birth_year": 2003, "class_id": 1},
        {"student_code": "2354050116", "name": "Phạm Thị D", "birth_year": 2003, "class_id": 4},
        {"student_code": "2354050117", "name": "Hoàng Văn E", "birth_year": 2003, "class_id": 5},
        {"student_code": "2354050118", "name": "Vũ Thị F", "birth_year": 2003, "class_id": 6},
        {"student_code": "2354050114", "name": "Trần Thị B", "birth_year": 2003, "class_id": 2},
        {"student_code": "2354050115", "name": "Lê Văn C", "birth_year": 2002, "class_id": 3},
    ],
    "users": [
        {"id": 1, "username": "admin", "password": "admin123", "role": "admin"},
        {"id": 2, "student_code": "2354050113", "password": "123456", "role": "student"},
        {"id": 5, "student_code": "2354050116", "password": "123456", "role": "student"},
        {"id": 6, "student_code": "2354050117", "password": "123456", "role": "student"},
        {"id": 7, "student_code": "2354050118", "password": "123456", "role": "student"},
        {"id": 3, "student_code": "2354050114", "password": "123456", "role": "student"},
        {"id": 4, "student_code": "2354050115", "password": "123456", "role": "student"},
    ],
    "courses": [
        {"id": 1, "name": "Kiểm thử phần mềm", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 2, "name": "Cấu trúc dữ liệu và giải thuật", "credits": 4, "faculty_id": 1, "is_shared": False},
        {"id": 3, "name": "Cơ sở dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 4, "name": "Phân tích thiết kế hệ thống", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 5, "name": "Lập trình Web", "credits": 4, "faculty_id": 1, "is_shared": False},
        {"id": 6, "name": "Mạng máy tính", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 11, "name": "Quản trị dự án phần mềm", "credits": 3, "faculty_id": 1, "is_shared": True},
        {"id": 12, "name": "Hệ hỗ trợ ra quyết định", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 13, "name": "Kho dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 14, "name": "Phân tích dữ liệu kinh doanh", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 15, "name": "Thiết kế giao diện người dùng", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 16, "name": "An toàn thông tin căn bản", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 17, "name": "Lập trình dịch vụ Web", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 18, "name": "Nhập môn hệ thống thông tin", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 19, "name": "Xác suất thống kê ứng dụng", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 20, "name": "Phân tích nghiệp vụ", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 21, "name": "Kiểm thử tự động", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 22, "name": "Chuyên đề tốt nghiệp 1", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 23, "name": "Nhập môn khoa học máy tính", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 24, "name": "Thuật toán nâng cao", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 25, "name": "Lập trình ứng dụng mạng", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 26, "name": "Bảo mật hệ thống", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 27, "name": "Chuyên đề tốt nghiệp 2", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 7, "name": "Nguyên lý kế toán", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 8, "name": "Tài chính doanh nghiệp", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 9, "name": "Marketing căn bản", "credits": 3, "faculty_id": 3, "is_shared": False},
        {"id": 10, "name": "Tin học đại cương", "credits": 2, "faculty_id": 1, "is_shared": True},
        {"id": 30, "name": "Xác suất và thống kê", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 31, "name": "Tiếng anh nâng cao 1", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 32, "name": "Tiếng anh nâng cao 2", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 33, "name": "Nhập môn tin học", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 34, "name": "Cơ sở lập trình", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 35, "name": "Giải tích", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 36, "name": "Tiếng anh nâng cao 3", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 37, "name": "Tiếng anh nâng cao 4", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 38, "name": "Kinh tế học đại cương", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 39, "name": "Kỹ thuật lập trình", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 40, "name": "Tiếng anh nâng cao 5", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 41, "name": "Đại số tuyến tính", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 42, "name": "Quản trị học", "credits": 3, "faculty_id": 3, "is_shared": True},
        {"id": 43, "name": "Hệ điều hành và kiến trúc máy tính", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 44, "name": "Triết học Mác-Lênin", "credits": 3, "faculty_id": 2, "is_shared": True},
        {"id": 45, "name": "Lập trình hướng đối tượng", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 46, "name": "Kinh tế chính trị Mác-Lênin", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 47, "name": "Chủ nghĩa xã hội khoa học", "credits": 3, "faculty_id": 2, "is_shared": True},
        {"id": 48, "name": "Kinh tế lượng", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 49, "name": "Lập trình giao diện", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 50, "name": "Lịch sử Đảng Cộng sản Việt Nam", "credits": 3, "faculty_id": 2, "is_shared": True},
        {"id": 51, "name": "Tư tưởng Hồ Chí Minh", "credits": 3, "faculty_id": 2, "is_shared": True},
        {"id": 52, "name": "Toán rời rạc", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 53, "name": "Hệ thống quản lí nguồn lực doanh nghiệp", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 54, "name": "Quản trị hệ cơ sở dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 55, "name": "Hệ thống thông tin quản lí", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 56, "name": "Dự báo trong kinh doanh", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 57, "name": "Môn chuyên ngành chọn 1", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 58, "name": "Lập trình cơ sở dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 59, "name": "Phát triển hệ thống thông tin quản lí", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 60, "name": "Môn chuyên ngành chọn 2", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 61, "name": "Đồ án ngành HTTTQL", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 62, "name": "Pháp luật đại cương", "credits": 3, "faculty_id": 3, "is_shared": True},
        {"id": 63, "name": "Lý luận nhà nước và pháp luật", "credits": 3, "faculty_id": 3, "is_shared": False},
        {"id": 64, "name": "Thực tập tốt nghiệp", "credits": 4, "faculty_id": 1, "is_shared": False},
        {"id": 65, "name": "Khóa luận tốt nghiệp", "credits": 6, "faculty_id": 1, "is_shared": False},
        {"id": 66, "name": "Môn thay thế khóa luận tốt nghiệp", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 67, "name": "Môn chuyên ngành chọn 3", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 68, "name": "Môn chuyên ngành chọn 4", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 69, "name": "Thiết kế Web", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 70, "name": "Mẫu thiết kế hướng đối tượng", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 71, "name": "Khai phá dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 72, "name": "Cơ sở dữ liệu phân tán", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 73, "name": "Quản trị mạng", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 74, "name": "Công nghệ phần mềm", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 75, "name": "Phân tích dữ liệu", "credits": 3, "faculty_id": 1, "is_shared": False},
        {"id": 76, "name": "Quản trị tài chính", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 77, "name": "Tiền tệ và ngân hàng", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 78, "name": "Kế toán tài chính 1", "credits": 3, "faculty_id": 2, "is_shared": False},
        {"id": 79, "name": "Quản trị nhân lực", "credits": 3, "faculty_id": 3, "is_shared": True},
        {"id": 80, "name": "Quản trị chuỗi cung ứng", "credits": 3, "faculty_id": 3, "is_shared": False},
        {"id": 81, "name": "Quản trị Marketing", "credits": 3, "faculty_id": 3, "is_shared": True},
        {"id": 82, "name": "Lập kế hoạch kinh doanh", "credits": 3, "faculty_id": 3, "is_shared": False},
    ],
    "course_majors": [
        {"course_id": 1, "major_id": 1},
        {"course_id": 2, "major_id": 1},
        {"course_id": 3, "major_id": 1},
        {"course_id": 4, "major_id": 1},
        {"course_id": 5, "major_id": 1},
        {"course_id": 6, "major_id": 1},
        {"course_id": 11, "major_id": 1},
        {"course_id": 12, "major_id": 1},
        {"course_id": 13, "major_id": 1},
        {"course_id": 14, "major_id": 1},
        {"course_id": 15, "major_id": 1},
        {"course_id": 16, "major_id": 1},
        {"course_id": 17, "major_id": 1},
        {"course_id": 18, "major_id": 1},
        {"course_id": 19, "major_id": 1},
        {"course_id": 20, "major_id": 1},
        {"course_id": 21, "major_id": 1},
        {"course_id": 22, "major_id": 1},
        {"course_id": 30, "major_id": 1},
        {"course_id": 31, "major_id": 1},
        {"course_id": 32, "major_id": 1},
        {"course_id": 33, "major_id": 1},
        {"course_id": 34, "major_id": 1},
        {"course_id": 35, "major_id": 1},
        {"course_id": 36, "major_id": 1},
        {"course_id": 37, "major_id": 1},
        {"course_id": 38, "major_id": 1},
        {"course_id": 39, "major_id": 1},
        {"course_id": 40, "major_id": 1},
        {"course_id": 41, "major_id": 1},
        {"course_id": 42, "major_id": 1},
        {"course_id": 43, "major_id": 1},
        {"course_id": 44, "major_id": 1},
        {"course_id": 45, "major_id": 1},
        {"course_id": 46, "major_id": 1},
        {"course_id": 47, "major_id": 1},
        {"course_id": 48, "major_id": 1},
        {"course_id": 49, "major_id": 1},
        {"course_id": 50, "major_id": 1},
        {"course_id": 51, "major_id": 1},
        {"course_id": 52, "major_id": 1},
        {"course_id": 53, "major_id": 1},
        {"course_id": 54, "major_id": 1},
        {"course_id": 55, "major_id": 1},
        {"course_id": 56, "major_id": 1},
        {"course_id": 57, "major_id": 1},
        {"course_id": 58, "major_id": 1},
        {"course_id": 59, "major_id": 1},
        {"course_id": 60, "major_id": 1},
        {"course_id": 61, "major_id": 1},
        {"course_id": 62, "major_id": 1},
        {"course_id": 63, "major_id": 1},
        {"course_id": 64, "major_id": 1},
        {"course_id": 65, "major_id": 1},
        {"course_id": 66, "major_id": 1},
        {"course_id": 67, "major_id": 1},
        {"course_id": 68, "major_id": 1},
        {"course_id": 69, "major_id": 1},
        {"course_id": 70, "major_id": 1},
        {"course_id": 71, "major_id": 1},
        {"course_id": 72, "major_id": 1},
        {"course_id": 73, "major_id": 1},
        {"course_id": 74, "major_id": 1},
        {"course_id": 75, "major_id": 1},
        {"course_id": 76, "major_id": 1},
        {"course_id": 77, "major_id": 1},
        {"course_id": 78, "major_id": 1},
        {"course_id": 79, "major_id": 1},
        {"course_id": 80, "major_id": 1},
        {"course_id": 81, "major_id": 1},
        {"course_id": 82, "major_id": 1},
        {"course_id": 2, "major_id": 2},
        {"course_id": 3, "major_id": 2},
        {"course_id": 5, "major_id": 2},
        {"course_id": 6, "major_id": 2},
        {"course_id": 15, "major_id": 2},
        {"course_id": 16, "major_id": 2},
        {"course_id": 17, "major_id": 2},
        {"course_id": 23, "major_id": 2},
        {"course_id": 24, "major_id": 2},
        {"course_id": 25, "major_id": 2},
        {"course_id": 26, "major_id": 2},
        {"course_id": 27, "major_id": 2},
        {"course_id": 7, "major_id": 3},
        {"course_id": 8, "major_id": 3},
        {"course_id": 9, "major_id": 4},
    ],
    "course_prerequisites": [
        {"course_id": 2, "prerequisite_id": 1},
        {"course_id": 4, "prerequisite_id": 3},
        {"course_id": 8, "prerequisite_id": 7},
    ],
    "training_program_courses": [
        {"training_program_id": 1, "course_id": 30, "semester_no": 1},
        {"training_program_id": 1, "course_id": 31, "semester_no": 1},
        {"training_program_id": 1, "course_id": 32, "semester_no": 1},
        {"training_program_id": 1, "course_id": 33, "semester_no": 1},
        {"training_program_id": 1, "course_id": 34, "semester_no": 1},
        {"training_program_id": 1, "course_id": 35, "semester_no": 2},
        {"training_program_id": 1, "course_id": 36, "semester_no": 2},
        {"training_program_id": 1, "course_id": 37, "semester_no": 2},
        {"training_program_id": 1, "course_id": 38, "semester_no": 2},
        {"training_program_id": 1, "course_id": 39, "semester_no": 2},
        {"training_program_id": 1, "course_id": 40, "semester_no": 3},
        {"training_program_id": 1, "course_id": 41, "semester_no": 3},
        {"training_program_id": 1, "course_id": 42, "semester_no": 3},
        {"training_program_id": 1, "course_id": 2, "semester_no": 3},
        {"training_program_id": 1, "course_id": 43, "semester_no": 3},
        {"training_program_id": 1, "course_id": 44, "semester_no": 4},
        {"training_program_id": 1, "course_id": 7, "semester_no": 4},
        {"training_program_id": 1, "course_id": 3, "semester_no": 4},
        {"training_program_id": 1, "course_id": 45, "semester_no": 4},
        {"training_program_id": 1, "course_id": 6, "semester_no": 4},
        {"training_program_id": 1, "course_id": 46, "semester_no": 5},
        {"training_program_id": 1, "course_id": 47, "semester_no": 5},
        {"training_program_id": 1, "course_id": 48, "semester_no": 5},
        {"training_program_id": 1, "course_id": 49, "semester_no": 5},
        {"training_program_id": 1, "course_id": 4, "semester_no": 5},
        {"training_program_id": 1, "course_id": 50, "semester_no": 6},
        {"training_program_id": 1, "course_id": 51, "semester_no": 6},
        {"training_program_id": 1, "course_id": 11, "semester_no": 6},
        {"training_program_id": 1, "course_id": 52, "semester_no": 6},
        {"training_program_id": 1, "course_id": 53, "semester_no": 6},
        {"training_program_id": 1, "course_id": 54, "semester_no": 7},
        {"training_program_id": 1, "course_id": 55, "semester_no": 7},
        {"training_program_id": 1, "course_id": 56, "semester_no": 7},
        {"training_program_id": 1, "course_id": 57, "semester_no": 7},
        {"training_program_id": 1, "course_id": 58, "semester_no": 8},
        {"training_program_id": 1, "course_id": 59, "semester_no": 8},
        {"training_program_id": 1, "course_id": 60, "semester_no": 8},
        {"training_program_id": 1, "course_id": 61, "semester_no": 9},
        {"training_program_id": 1, "course_id": 62, "semester_no": 9},
        {"training_program_id": 1, "course_id": 63, "semester_no": 9},
        {"training_program_id": 1, "course_id": 64, "semester_no": 10},
        {"training_program_id": 1, "course_id": 65, "semester_no": 11},
        {"training_program_id": 1, "course_id": 66, "semester_no": 11},
        {"training_program_id": 1, "course_id": 67, "semester_no": 11},
        {"training_program_id": 1, "course_id": 68, "semester_no": 11},
        {"training_program_id": 1, "course_id": 69, "semester_no": 8},
        {"training_program_id": 1, "course_id": 5, "semester_no": 8},
        {"training_program_id": 1, "course_id": 70, "semester_no": 8},
        {"training_program_id": 1, "course_id": 71, "semester_no": 8},
        {"training_program_id": 1, "course_id": 72, "semester_no": 8},
        {"training_program_id": 1, "course_id": 73, "semester_no": 8},
        {"training_program_id": 1, "course_id": 74, "semester_no": 8},
        {"training_program_id": 1, "course_id": 1, "semester_no": 8},
        {"training_program_id": 1, "course_id": 75, "semester_no": 8},
        {"training_program_id": 1, "course_id": 76, "semester_no": 11},
        {"training_program_id": 1, "course_id": 77, "semester_no": 11},
        {"training_program_id": 1, "course_id": 78, "semester_no": 11},
        {"training_program_id": 1, "course_id": 79, "semester_no": 11},
        {"training_program_id": 1, "course_id": 80, "semester_no": 11},
        {"training_program_id": 1, "course_id": 81, "semester_no": 11},
        {"training_program_id": 1, "course_id": 82, "semester_no": 11},

        {"training_program_id": 5, "course_id": 10, "semester_no": 1},
        {"training_program_id": 5, "course_id": 23, "semester_no": 2},
        {"training_program_id": 5, "course_id": 3, "semester_no": 3},
        {"training_program_id": 5, "course_id": 2, "semester_no": 4},
        {"training_program_id": 5, "course_id": 24, "semester_no": 5},
        {"training_program_id": 5, "course_id": 15, "semester_no": 6},
        {"training_program_id": 5, "course_id": 16, "semester_no": 6},
        {"training_program_id": 5, "course_id": 17, "semester_no": 6},
        {"training_program_id": 5, "course_id": 6, "semester_no": 4},
        {"training_program_id": 5, "course_id": 5, "semester_no": 4},
        {"training_program_id": 5, "course_id": 11, "semester_no": 4},
        {"training_program_id": 5, "course_id": 25, "semester_no": 7},
        {"training_program_id": 5, "course_id": 14, "semester_no": 8},
        {"training_program_id": 5, "course_id": 69, "semester_no": 8},
        {"training_program_id": 5, "course_id": 73, "semester_no": 8},
        {"training_program_id": 5, "course_id": 42, "semester_no": 3},
        {"training_program_id": 5, "course_id": 44, "semester_no": 4},
        {"training_program_id": 5, "course_id": 47, "semester_no": 5},
        {"training_program_id": 5, "course_id": 50, "semester_no": 6},
        {"training_program_id": 5, "course_id": 51, "semester_no": 6},
        {"training_program_id": 5, "course_id": 79, "semester_no": 8},
        {"training_program_id": 5, "course_id": 81, "semester_no": 8},
        {"training_program_id": 5, "course_id": 26, "semester_no": 9},
        {"training_program_id": 5, "course_id": 71, "semester_no": 9},
        {"training_program_id": 5, "course_id": 62, "semester_no": 9},
        {"training_program_id": 5, "course_id": 13, "semester_no": 10},
        {"training_program_id": 5, "course_id": 27, "semester_no": 11},

        {"training_program_id": 2, "course_id": 10, "semester_no": 1},
        {"training_program_id": 2, "course_id": 7, "semester_no": 2},
        {"training_program_id": 2, "course_id": 42, "semester_no": 2},
        {"training_program_id": 2, "course_id": 44, "semester_no": 3},
        {"training_program_id": 2, "course_id": 8, "semester_no": 4},
        {"training_program_id": 2, "course_id": 47, "semester_no": 4},
        {"training_program_id": 2, "course_id": 50, "semester_no": 5},
        {"training_program_id": 2, "course_id": 51, "semester_no": 5},
        {"training_program_id": 2, "course_id": 62, "semester_no": 6},
        {"training_program_id": 2, "course_id": 76, "semester_no": 6},
        {"training_program_id": 2, "course_id": 77, "semester_no": 7},
        {"training_program_id": 2, "course_id": 78, "semester_no": 7},
        {"training_program_id": 2, "course_id": 79, "semester_no": 8},
        {"training_program_id": 2, "course_id": 81, "semester_no": 8},

        {"training_program_id": 3, "course_id": 10, "semester_no": 1},
        {"training_program_id": 3, "course_id": 42, "semester_no": 2},
        {"training_program_id": 3, "course_id": 9, "semester_no": 3},
        {"training_program_id": 3, "course_id": 44, "semester_no": 3},
        {"training_program_id": 3, "course_id": 47, "semester_no": 4},
        {"training_program_id": 3, "course_id": 50, "semester_no": 5},
        {"training_program_id": 3, "course_id": 51, "semester_no": 5},
        {"training_program_id": 3, "course_id": 62, "semester_no": 6},
        {"training_program_id": 3, "course_id": 79, "semester_no": 7},
        {"training_program_id": 3, "course_id": 81, "semester_no": 7},
        {"training_program_id": 3, "course_id": 82, "semester_no": 8},
        {"training_program_id": 3, "course_id": 76, "semester_no": 8},
    ],
    "teachers": [
        {"id": 1, "name": "Thầy B", "faculty_id": 1},
        {"id": 2, "name": "Cô C", "faculty_id": 1},
        {"id": 3, "name": "Thầy D", "faculty_id": 1},
        {"id": 4, "name": "Thầy K", "faculty_id": 2},
        {"id": 5, "name": "Cô M", "faculty_id": 3},
    ],
    "rooms": [
        {"id": 1, "name": "A101", "room_type": "theory", "capacity": 50, "campus_id": 1},
        {"id": 2, "name": "A102", "room_type": "theory", "capacity": 45, "campus_id": 1},
        {"id": 3, "name": "B201", "room_type": "theory", "capacity": 50, "campus_id": 1},
        {"id": 4, "name": "TH01", "room_type": "practice", "capacity": 50, "campus_id": 1},
        {"id": 5, "name": "TH02", "room_type": "practice", "capacity": 35, "campus_id": 1},
        {"id": 6, "name": "C201", "room_type": "theory", "capacity": 50, "campus_id": 2},
        {"id": 7, "name": "C202", "room_type": "theory", "capacity": 45, "campus_id": 2},
        {"id": 8, "name": "C203", "room_type": "theory", "capacity": 50, "campus_id": 2},
        {"id": 9, "name": "D301", "room_type": "theory", "capacity": 50, "campus_id": 3},
        {"id": 10, "name": "D302", "room_type": "theory", "capacity": 45, "campus_id": 3},
        {"id": 11, "name": "D303", "room_type": "theory", "capacity": 50, "campus_id": 3},
    ],
    "campuses": [
        {"id": 1, "name": "Cơ sở 1", "address": "TPHCM"},
        {"id": 2, "name": "Cơ sở 2", "address": "TPHCM"},
        {"id": 3, "name": "Cơ sở 3", "address": "TPHCM"},
    ],
    "class_sections": [
        {"id": 1, "name": "DH23IM01", "student_class_id": 1, "course_id": 53, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 50, "start_date": "2025-09-01", "end_date": "2025-12-01", "registration_deadline": "2025-08-25"},
        {"id": 2, "name": "DH23CS01", "student_class_id": 5, "course_id": 2, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-03", "end_date": "2025-12-05", "registration_deadline": "2025-08-25"},
        {"id": 10, "name": "DH23IM02", "student_class_id": 4, "course_id": 3, "teacher_id": 2, "room_id": 4, "semester": "2025-1", "max_students": 50, "start_date": "2025-09-04", "end_date": "2025-12-10", "registration_deadline": "2025-08-25", "section_type": "practice"},
        {"id": 3, "name": "DH23IM02", "student_class_id": 4, "course_id": 3, "teacher_id": 1, "room_id": 3, "semester": "2025-1", "max_students": 50, "start_date": "2025-09-04", "end_date": "2025-12-10", "registration_deadline": "2025-08-25", "linked_section_id": 10},
        {"id": 4, "name": "DH23IM01", "student_class_id": 1, "course_id": 51, "teacher_id": 3, "room_id": 1, "semester": "2025-1", "max_students": 40, "start_date": "2025-09-05", "end_date": "2025-12-12", "registration_deadline": "2025-08-25"},
        {"id": 11, "name": "DH23CS02", "student_class_id": 6, "course_id": 5, "teacher_id": 3, "room_id": 5, "semester": "2025-1", "max_students": 35, "start_date": "2025-09-06", "end_date": "2025-12-15", "registration_deadline": "2025-08-25", "section_type": "practice"},
        {"id": 5, "name": "DH23CS02", "student_class_id": 6, "course_id": 5, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 35, "start_date": "2025-09-06", "end_date": "2025-12-15", "registration_deadline": "2025-08-25", "linked_section_id": 11},
        {"id": 6, "name": "DH23CS01", "student_class_id": 5, "course_id": 6, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 50, "start_date": "2025-09-07", "end_date": "2025-12-18", "registration_deadline": "2025-08-25"},
        {"id": 12, "name": "DH23IM02", "student_class_id": 4, "course_id": 11, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-11", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 13, "name": "DH23IM02", "student_class_id": 4, "course_id": 50, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-12", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 14, "name": "DH23IM01", "student_class_id": 1, "course_id": 52, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 40, "start_date": "2025-09-13", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 15, "name": "DH23IM01", "student_class_id": 1, "course_id": 54, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-14", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 16, "name": "DH23CS01", "student_class_id": 5, "course_id": 15, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-15", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 17, "name": "DH23CS02", "student_class_id": 6, "course_id": 16, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-16", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 18, "name": "DH23CS01", "student_class_id": 5, "course_id": 17, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-17", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 19, "name": "DH23IM01", "student_class_id": 1, "course_id": 34, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-18", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 20, "name": "DH23IM02", "student_class_id": 4, "course_id": 39, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-19", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 21, "name": "DH23IM01", "student_class_id": 1, "course_id": 40, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-20", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 22, "name": "DH23IM02", "student_class_id": 4, "course_id": 45, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-21", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 23, "name": "DH23IM01", "student_class_id": 1, "course_id": 49, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-22", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 24, "name": "DH23IM02", "student_class_id": 4, "course_id": 54, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-23", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 25, "name": "DH23IM01", "student_class_id": 1, "course_id": 58, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-24", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 26, "name": "DH23IM02", "student_class_id": 4, "course_id": 61, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-25", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 27, "name": "DH23IM01", "student_class_id": 1, "course_id": 64, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-26", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 28, "name": "DH23IM02", "student_class_id": 4, "course_id": 65, "teacher_id": 1, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-27", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 30, "name": "DH23IM02", "student_class_id": 4, "course_id": 31, "teacher_id": 3, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-29", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 31, "name": "DH23IM01", "student_class_id": 1, "course_id": 32, "teacher_id": 1, "room_id": 3, "semester": "2025-1", "max_students": 50, "start_date": "2025-09-30", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 32, "name": "DH23IM02", "student_class_id": 4, "course_id": 33, "teacher_id": 2, "room_id": 1, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-01", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 33, "name": "DH23IM01", "student_class_id": 1, "course_id": 35, "teacher_id": 3, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-02", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 37, "name": "DH23IM01", "student_class_id": 1, "course_id": 41, "teacher_id": 3, "room_id": 3, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-06", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 38, "name": "DH23IM02", "student_class_id": 4, "course_id": 43, "teacher_id": 1, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-07", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 39, "name": "DH23IM01", "student_class_id": 1, "course_id": 44, "teacher_id": 4, "room_id": 3, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-08", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 41, "name": "DH23IM01", "student_class_id": 1, "course_id": 46, "teacher_id": 4, "room_id": 1, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-10", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 42, "name": "DH23IM02", "student_class_id": 4, "course_id": 47, "teacher_id": 4, "room_id": 3, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-11", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 44, "name": "DH23IM02", "student_class_id": 4, "course_id": 4, "teacher_id": 2, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-13", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 45, "name": "DH23CS01", "student_class_id": 5, "course_id": 23, "teacher_id": 1, "room_id": 6, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-14", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 46, "name": "DH23CS02", "student_class_id": 6, "course_id": 24, "teacher_id": 2, "room_id": 7, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-15", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 47, "name": "DH23CS01", "student_class_id": 5, "course_id": 25, "teacher_id": 3, "room_id": 8, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-16", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 48, "name": "DH23CS02", "student_class_id": 6, "course_id": 26, "teacher_id": 1, "room_id": 9, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-17", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 49, "name": "DH23TC01", "student_class_id": 2, "course_id": 76, "teacher_id": 4, "room_id": 10, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-18", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 50, "name": "DH23TC01", "student_class_id": 2, "course_id": 77, "teacher_id": 4, "room_id": 11, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-19", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 51, "name": "DH23TC01", "student_class_id": 2, "course_id": 78, "teacher_id": 4, "room_id": 6, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-20", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 52, "name": "DH22MK01", "student_class_id": 3, "course_id": 79, "teacher_id": 5, "room_id": 7, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-21", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 53, "name": "DH22MK01", "student_class_id": 3, "course_id": 81, "teacher_id": 5, "room_id": 8, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-22", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 54, "name": "DH22MK01", "student_class_id": 3, "course_id": 82, "teacher_id": 5, "room_id": 9, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-23", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 55, "name": "DH23CS01", "student_class_id": 5, "course_id": 42, "teacher_id": 5, "room_id": 10, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-24", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 56, "name": "DH23TC01", "student_class_id": 2, "course_id": 62, "teacher_id": 5, "room_id": 11, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-25", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 57, "name": "DH22MK01", "student_class_id": 3, "course_id": 50, "teacher_id": 4, "room_id": 6, "semester": "2025-1", "max_students": 50, "start_date": "2025-10-26", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 58, "name": "DH23CS02", "student_class_id": 6, "course_id": 11, "teacher_id": 1, "room_id": 7, "semester": "2025-1", "max_students": 45, "start_date": "2025-10-27", "end_date": "2025-12-22", "registration_deadline": "2025-08-25"},
        {"id": 7, "name": "DH23TC01", "student_class_id": 2, "course_id": 7, "teacher_id": 4, "room_id": 1, "semester": "2025-1", "max_students": 50, "start_date": "2025-09-08", "end_date": "2025-12-19", "registration_deadline": "2025-08-25"},
        {"id": 8, "name": "DH23TC01", "student_class_id": 2, "course_id": 8, "teacher_id": 4, "room_id": 2, "semester": "2025-1", "max_students": 45, "start_date": "2025-09-09", "end_date": "2025-12-20", "registration_deadline": "2025-08-25"},
        {"id": 9, "name": "DH22MK01", "student_class_id": 3, "course_id": 9, "teacher_id": 5, "room_id": 3, "semester": "2025-1", "max_students": 40, "start_date": "2025-09-10", "end_date": "2025-12-21", "registration_deadline": "2025-08-25"},
    ],
    "schedules": [
        {"id": 1, "class_section_id": 1, "day_of_week": 2, "start_time": "07:00", "end_time": "11:30"},
        {"id": 2, "class_section_id": 2, "day_of_week": 3, "start_time": "07:00", "end_time": "11:30"},
        {"id": 10, "class_section_id": 10, "day_of_week": 6, "start_time": "07:00", "end_time": "09:30"},
        {"id": 3, "class_section_id": 3, "day_of_week": 4, "start_time": "13:00", "end_time": "17:30"},
        {"id": 4, "class_section_id": 4, "day_of_week": 5, "start_time": "07:00", "end_time": "11:30"},
        {"id": 11, "class_section_id": 11, "day_of_week": 7, "start_time": "07:00", "end_time": "09:30"},
        {"id": 5, "class_section_id": 5, "day_of_week": 6, "start_time": "13:00", "end_time": "17:30"},
        {"id": 6, "class_section_id": 6, "day_of_week": 7, "start_time": "07:00", "end_time": "11:30"},
        {"id": 12, "class_section_id": 12, "day_of_week": 6, "start_time": "07:00", "end_time": "11:30"},
        {"id": 13, "class_section_id": 13, "day_of_week": 3, "start_time": "13:00", "end_time": "17:30"},
        {"id": 14, "class_section_id": 14, "day_of_week": 5, "start_time": "13:00", "end_time": "17:30"},
        {"id": 15, "class_section_id": 15, "day_of_week": 3, "start_time": "13:00", "end_time": "16:30"},
        {"id": 16, "class_section_id": 16, "day_of_week": 5, "start_time": "07:00", "end_time": "10:30"},
        {"id": 17, "class_section_id": 17, "day_of_week": 2, "start_time": "13:00", "end_time": "16:30"},
        {"id": 18, "class_section_id": 18, "day_of_week": 7, "start_time": "07:00", "end_time": "10:30"},
        {"id": 19, "class_section_id": 19, "day_of_week": 3, "start_time": "07:00", "end_time": "10:30"},
        {"id": 20, "class_section_id": 20, "day_of_week": 4, "start_time": "13:00", "end_time": "16:30"},
        {"id": 21, "class_section_id": 21, "day_of_week": 4, "start_time": "07:00", "end_time": "10:30"},
        {"id": 22, "class_section_id": 22, "day_of_week": 5, "start_time": "13:00", "end_time": "16:30"},
        {"id": 23, "class_section_id": 23, "day_of_week": 6, "start_time": "07:00", "end_time": "10:30"},
        {"id": 24, "class_section_id": 24, "day_of_week": 7, "start_time": "13:00", "end_time": "16:30"},
        {"id": 25, "class_section_id": 25, "day_of_week": 7, "start_time": "13:00", "end_time": "16:30"},
        {"id": 26, "class_section_id": 26, "day_of_week": 2, "start_time": "13:00", "end_time": "16:30"},
        {"id": 27, "class_section_id": 27, "day_of_week": 2, "start_time": "07:00", "end_time": "10:30"},
        {"id": 28, "class_section_id": 28, "day_of_week": 6, "start_time": "13:00", "end_time": "16:30"},
        {"id": 30, "class_section_id": 30, "day_of_week": 2, "start_time": "07:00", "end_time": "10:30"},
        {"id": 31, "class_section_id": 31, "day_of_week": 3, "start_time": "13:00", "end_time": "16:30"},
        {"id": 32, "class_section_id": 32, "day_of_week": 4, "start_time": "07:00", "end_time": "10:30"},
        {"id": 33, "class_section_id": 33, "day_of_week": 7, "start_time": "07:00", "end_time": "10:30"},
        {"id": 37, "class_section_id": 37, "day_of_week": 3, "start_time": "07:00", "end_time": "10:30"},
        {"id": 38, "class_section_id": 38, "day_of_week": 7, "start_time": "13:00", "end_time": "16:30"},
        {"id": 39, "class_section_id": 39, "day_of_week": 5, "start_time": "07:00", "end_time": "10:30"},
        {"id": 41, "class_section_id": 41, "day_of_week": 4, "start_time": "13:00", "end_time": "16:30"},
        {"id": 42, "class_section_id": 42, "day_of_week": 6, "start_time": "07:00", "end_time": "10:30"},
        {"id": 44, "class_section_id": 44, "day_of_week": 5, "start_time": "13:00", "end_time": "16:30"},
        {"id": 45, "class_section_id": 45, "day_of_week": 2, "start_time": "07:00", "end_time": "10:30"},
        {"id": 46, "class_section_id": 46, "day_of_week": 2, "start_time": "07:00", "end_time": "10:30"},
        {"id": 47, "class_section_id": 47, "day_of_week": 2, "start_time": "07:00", "end_time": "10:30"},
        {"id": 48, "class_section_id": 48, "day_of_week": 2, "start_time": "07:00", "end_time": "10:30"},
        {"id": 49, "class_section_id": 49, "day_of_week": 3, "start_time": "07:00", "end_time": "10:30"},
        {"id": 50, "class_section_id": 50, "day_of_week": 3, "start_time": "07:00", "end_time": "10:30"},
        {"id": 51, "class_section_id": 51, "day_of_week": 4, "start_time": "07:00", "end_time": "10:30"},
        {"id": 52, "class_section_id": 52, "day_of_week": 4, "start_time": "07:00", "end_time": "10:30"},
        {"id": 53, "class_section_id": 53, "day_of_week": 4, "start_time": "07:00", "end_time": "10:30"},
        {"id": 54, "class_section_id": 54, "day_of_week": 4, "start_time": "07:00", "end_time": "10:30"},
        {"id": 55, "class_section_id": 55, "day_of_week": 5, "start_time": "13:00", "end_time": "16:30"},
        {"id": 56, "class_section_id": 56, "day_of_week": 5, "start_time": "13:00", "end_time": "16:30"},
        {"id": 57, "class_section_id": 57, "day_of_week": 6, "start_time": "07:00", "end_time": "10:30"},
        {"id": 58, "class_section_id": 58, "day_of_week": 6, "start_time": "07:00", "end_time": "10:30"},
        {"id": 7, "class_section_id": 7, "day_of_week": 2, "start_time": "13:00", "end_time": "17:30"},
        {"id": 8, "class_section_id": 8, "day_of_week": 4, "start_time": "07:00", "end_time": "11:30"},
        {"id": 9, "class_section_id": 9, "day_of_week": 6, "start_time": "13:00", "end_time": "17:30"},
    ],
    "enrollments": [
        {"id": 1, "student_code": "2354050113", "class_section_id": 1, "status": "registered"},
        {"id": 2, "student_code": "2354050113", "class_section_id": 3, "status": "registered"},
        {"id": 3, "student_code": "2354050113", "class_section_id": 5, "status": "canceled"},
        {"id": 6, "student_code": "2354050116", "class_section_id": 2, "status": "registered"},
        {"id": 7, "student_code": "2354050117", "class_section_id": 2, "status": "registered"},
        {"id": 8, "student_code": "2354050118", "class_section_id": 6, "status": "registered"},
        {"id": 4, "student_code": "2354050114", "class_section_id": 7, "status": "registered"},
        {"id": 5, "student_code": "2354050115", "class_section_id": 9, "status": "registered"},
    ],
}


def seed_data():
    db.drop_all()
    db.create_all()

    for faculty in sample_data["faculties"]:
        db.session.add(Faculty(id=faculty["id"], name=faculty["name"]))
    db.session.commit()

    for major in sample_data["majors"]:
        db.session.add(Major(id=major["id"], name=major["name"], faculty_id=major["faculty_id"]))
    db.session.commit()

    for student_class in sample_data["student_classes"]:
        db.session.add(
            StudentClass(
                id=student_class["id"],
                code=student_class["code"],
                name=student_class["name"],
                school_year=student_class["school_year"],
                major_id=student_class["major_id"],
            )
        )
    db.session.commit()

    for training_program in sample_data.get("training_programs", []):
        db.session.add(
            TrainingProgram(
                id=training_program["id"],
                name=training_program["name"],
                major_id=training_program["major_id"],
                school_year=training_program["school_year"],
                max_credits_per_semester=training_program.get("max_credits_per_semester", 25),
            )
        )
    db.session.commit()

    for student in sample_data["students"]:
        db.session.add(
            Student(
                student_code=student["student_code"],
                name=student["name"],
                birth_year=student["birth_year"],
                major_id=next(
                    item["major_id"]
                    for item in sample_data["student_classes"]
                    if item["id"] == student["class_id"]
                ),
                class_id=student["class_id"],
            )
        )
    db.session.commit()

    for user_data in sample_data["users"]:
        role = UserRole(user_data["role"])
        user = User(
            id=user_data["id"],
            username=user_data.get("username"),
            password=hashlib.md5(user_data["password"].strip().encode("utf-8")).hexdigest(),
            role=role,
        )

        if role == UserRole.STUDENT:
            user.student_code = user_data["student_code"]

        db.session.add(user)
    db.session.commit()

    for campus in sample_data["campuses"]:
        db.session.add(Campus(id=campus["id"], name=campus["name"], address=campus["address"]))
    db.session.commit()

    for room in sample_data["rooms"]:
        db.session.add(
            Room(
                id=room["id"],
                name=room["name"],
                room_type=room.get("room_type"),
                capacity=room["capacity"],
                campus_id=room["campus_id"],
            )
        )
    db.session.commit()

    for course in sample_data["courses"]:
        db.session.add(
            Course(
                id=course["id"],
                name=course["name"],
                credits=course["credits"],
                faculty_id=course["faculty_id"],
                is_shared=course.get("is_shared", False),
            )
        )
    db.session.commit()

    for course_major in sample_data.get("course_majors", []):
        db.session.add(
            CourseMajor(
                course_id=course_major["course_id"],
                major_id=course_major["major_id"],
            )
        )
    db.session.commit()

    for prerequisite in sample_data.get("course_prerequisites", []):
        db.session.add(
            CoursePrerequisite(
                course_id=prerequisite["course_id"],
                prerequisite_id=prerequisite["prerequisite_id"],
            )
        )
    db.session.commit()

    for training_program_course in sample_data.get("training_program_courses", []):
        db.session.add(
            TrainingProgramCourse(
                training_program_id=training_program_course["training_program_id"],
                course_id=training_program_course["course_id"],
                semester_no=training_program_course.get("semester_no", 1),
            )
        )
    db.session.commit()

    for teacher in sample_data["teachers"]:
        db.session.add(Teacher(id=teacher["id"], name=teacher["name"], faculty_id=teacher["faculty_id"]))
    db.session.commit()

    for class_section in sample_data["class_sections"]:
        db.session.add(
            ClassSection(
                id=class_section["id"],
                name=class_section.get("name"),
                student_class_id=class_section.get("student_class_id"),
                course_id=class_section["course_id"],
                teacher_id=class_section["teacher_id"],
                room_id=class_section["room_id"],
                semester=class_section["semester"],
                max_students=class_section["max_students"],
                start_date=datetime.fromisoformat(class_section["start_date"]),
                end_date=datetime.fromisoformat(class_section["end_date"]),
                registration_deadline=datetime.fromisoformat(class_section["registration_deadline"]),
                section_type=ClassSectionType(class_section.get("section_type", "theory")),
                linked_section_id=class_section.get("linked_section_id"),
            )
        )
    db.session.commit()

    for schedule in sample_data["schedules"]:
        db.session.add(
            Schedule(
                id=schedule["id"],
                class_section_id=schedule["class_section_id"],
                day_of_week=schedule["day_of_week"],
                start_time=datetime.strptime(schedule["start_time"], "%H:%M").time(),
                end_time=datetime.strptime(schedule["end_time"], "%H:%M").time(),
            )
        )
    db.session.commit()

    for enrollment in sample_data["enrollments"]:
        db.session.add(
            Enrollment(
                id=enrollment["id"],
                student_code=enrollment["student_code"],
                class_section_id=enrollment["class_section_id"],
                status=EnrollmentStatus(enrollment["status"]),
                registered_at=datetime.fromisoformat(enrollment["registered_at"])
                if enrollment.get("registered_at")
                else None,
            )
        )
    db.session.commit()

    print("Seed full data thành công!")


if __name__ == "__main__":
    with app.app_context():
        seed_data()
