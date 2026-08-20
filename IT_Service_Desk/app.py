from flask import Flask, redirect, url_for

from config.database import init_db

from controllers.user_controller import user_controller


app = Flask(__name__)
app.config["SECRET_KEY"] = "changeme"
init_db(app)
app.register_blueprint(
    user_controller
)
@app.route("/")
def home():

    return redirect(
        url_for("user_controller.login")
    )


if __name__ == "__main__":

    app.run(
        debug=True
    )