import os
from flask import Flask, redirect, url_for
from config.database import init_db
from utils.time_v import to_local_time
from controllers.user_controller import user_controller
from controllers.ticket_controller import ticket_controller
from controllers.ticket_assignment_controller import ticket_assignment_bp
from controllers.admin_user_controller import admin_user_bp
from controllers.admin_ticket_controller import admin_ticket_bp
from controllers.admin_report_controller import admin_report_bp
from controllers.api_controller import api_bp
from controllers.admin_sla_rule_controller import admin_sla_rule_bp
from controllers.admin_category_controller import admin_category_bp
from controllers.feedback_controller import feedback_bp

app = Flask(__name__)
app.jinja_env.filters["localtime"] = to_local_time

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_EXPIRES_MINUTES"] = int(
    os.getenv("JWT_EXPIRES_MINUTES", "15")
)
app.config["JWT_COOKIE_SECURE"] = os.getenv(
    "JWT_COOKIE_SECURE",
    "0"
) == "1"

init_db(app)

app.register_blueprint(user_controller)
app.register_blueprint(ticket_controller)
app.register_blueprint(ticket_assignment_bp)
app.register_blueprint(admin_user_bp)
app.register_blueprint(admin_ticket_bp)
app.register_blueprint(admin_report_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_sla_rule_bp)
app.register_blueprint(admin_category_bp)
app.register_blueprint(feedback_bp)

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

@app.route("/")
def home():
    return redirect(
        url_for("user_controller.login")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)