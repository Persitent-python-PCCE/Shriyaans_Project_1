from flask import Flask
from config.database import init_db
name=Flask(__name__)
init_db(name)
@name.route("/")
def home():
    return "Server connected and running "
if __name__=="__main__":
    name.run(debug=True)