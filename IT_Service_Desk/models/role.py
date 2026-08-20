from config.database import db
class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    users = db.relationship(
        "User",
        back_populates="role"
    )

    def __repr__(self):
        return f"<Role {self.name}>"