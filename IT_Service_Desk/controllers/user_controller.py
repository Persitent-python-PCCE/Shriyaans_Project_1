from flask import Blueprint,request,render_template,redirect,url_for,session
from services.user_service import UserService
from models.role import Role
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError
user_controller = Blueprint("user_controller",__name__)
user_service = UserService()
@user_controller.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_page.html")
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return render_template(
            "login_page.html",
            error="Email and password are required."
        )

    user = user_service.get_user_by_email(email)

    if not user:
        return render_template(
            "login_page.html",
            error="Invalid email or password."
        )

    if not user.is_active:
        return render_template(
            "login_page.html",
            error="Your account is inactive."
        )

    if not check_password_hash(user.password_hash, password):
        return render_template(
            "login_page.html",
            error="Invalid email or password."
        )

     
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email
    session["role"] = user.role.name

     
    if user.role.name == "EMPLOYEE":
        return redirect(url_for("user_controller.employee_dashboard"))

    elif user.role.name == "AGENT":
        return redirect(url_for("user_controller.agent_dashboard"))

    elif user.role.name == "ADMIN":
        return redirect(url_for("user_controller.admin_dashboard"))

    return render_template(
        "login_page.html",
        error="Invalid user role."
    )

 

@user_controller.route("/users/add", methods=["GET", "POST"])
def register():

     
    if request.method == "GET":
        return render_template("login_page.html",register=True)

    data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "password": request.form.get("password"),
        "role_id": request.form.get("role_id")
    }

    try:

        user_service.create_user(data)

        # Registration successful
        return redirect(url_for("user_controller.login"))

    except ValueError as e:

        return render_template(
            "login_page.html",
            error=str(e)
        )

    except IntegrityError:

        return render_template(
            "login_page.html",
            error="Database constraint error. Please check your details.",register=True
        )

    except Exception:

        return render_template(
            "login_page.html",
            error="Something went wrong while creating the account.",register=True
        )
 

@user_controller.route("/employee/dashboard")
def employee_dashboard():

    if "user_id" not in session:
        return redirect(url_for("user_controller.login"))

    if session.get("role") != "EMPLOYEE":
        return "Unauthorized", 403

    return render_template(
        "employee_dashboard.html",
        name=session.get("user_name"),
        email=session.get("user_email"),
        role=session.get("role")
    )

 
@user_controller.route("/agent/dashboard")
def agent_dashboard():

    if "user_id" not in session:
        return redirect(url_for("user_controller.login"))

    if session.get("role") != "AGENT":
        return "Unauthorized", 403

    return render_template(
        "agent_dashboard.html",
        name=session.get("user_name"),
        email=session.get("user_email"),
        role=session.get("role")
    )


@user_controller.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("user_controller.login"))

    if session.get("role") != "ADMIN":
        return "Unauthorized", 403

    return render_template(
        "admin_dashboard.html",
        name=session.get("user_name"),
        email=session.get("user_email"),
        role=session.get("role")
    )

@user_controller.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("user_controller.login")
    )