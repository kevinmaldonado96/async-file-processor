from modelos import db, Users


class UserRepository:

    def obtener_por_email(self, email):
        return Users.query.filter_by(email=email).first()

    def obtener_por_username(self, username):
        return Users.query.filter_by(username=username).first()

    def guardar_usuario(self, user):
        db.session.add(user)
        db.session.commit()

    def obtener_usuario_por_id(self, id):
        return Users.query.filter_by(id=id).first()
