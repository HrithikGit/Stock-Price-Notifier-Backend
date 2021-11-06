from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    phone = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(30))

    def __repr__(self) -> str:
        return self.name+' '+self.phone+' '+self.password


class Stock(db.Model):
    __tablename__ = 'stock'
    stock_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    symbol = db.Column(db.String(30))
    industry = db.Column(db.String(30))

    def __repr__(self) -> str:
        return f"{self.name} - {self.symbol}"


class UserStock(db.Model):
    __tablename__ = 'userStock'
    user_stock_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    stock_id = db.Column(db.Integer)

    def __repr__(self) -> str:
        return f"{self.user_id} - {self.stock_id}"
