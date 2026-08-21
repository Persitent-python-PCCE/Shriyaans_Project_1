from flask import Flask, redirect, url_for

from config.database import init_db

from controllers.user_controller import user_controller
from controllers.ticket_controller import ticket_controller
from controllers.ticket_assignment_controller import ticket_assignment_bp
from controllers.admin_user_controller import admin_user_bp
from controllers.admin_ticket_controller import admin_ticket_bp


app = Flask(__name__)

app.config["SECRET_KEY"] = "changeme"

init_db(app)

app.register_blueprint(user_controller)
app.register_blueprint(ticket_controller)
app.register_blueprint(ticket_assignment_bp)
app.register_blueprint(admin_user_bp)
app.register_blueprint(admin_ticket_bp)


@app.route("/")
def home():
    return redirect(
        url_for("user_controller.login")
    )


if __name__ == "__main__":
    app.run(debug=True)