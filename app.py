from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from functools import wraps
import csv
import jwt
from json import dumps
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'HRI$8934'
CORS(app)

db = SQLAlchemy(app)


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


def addAllStocks():
    with open('Equity.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        count = 0
        for row in csv_reader:
            if(count == 0):
                count = 1
                continue
            new_stock = Stock(name=row[3], symbol=row[2], industry=row[8])
            db.session.add(new_stock)
    db.session.commit()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms="HS256")
            print(data)
            current_user = User.query.filter_by(
                phone=data['phone']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/login', methods=["POST"])
def login():
    data = None
    if(request.method == "POST"):
        data = request.get_json()
        try:
            username = data['phone']
            password = data['password']
        except:
            return jsonify({"error": "Required fields are missing, Please Check Again"})
        user = User.query.filter_by(phone=username).first()

        if(user is None):
            return jsonify({"status": "error", "message": "User does not exist"})
        if(user.password != password):
            return jsonify({"status": "error", "message": "Wrong password"})

        token = jwt.encode({
            'phone': user.phone,
            'name': user.name
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"status": "success", "message": "User logged in", "token": token, "name": user.name})


@app.route('/register', methods=["POST"])
def register():
    data = None
    if(request.method == "POST"):
        data = request.get_json()
        name, phone, password = None, None, None
        try:
            name = data['name']
            phone = data['phone']
            password = data['password']
        except:
            return jsonify({"message": "Required fields are missing, Please Check Again"})
        user = User.query.filter_by(phone=phone).first()

        if(user is not None):
            return jsonify({"status": "error", "message": "User already exists"})

        new_user = User(name=name, phone=phone, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"status": "success", "message": "User registered"})


@app.route("/getStocksList", methods=["POST"])
@token_required
def get_stocks_list(current_user):
    data = request.get_json()
    name = data['name']
    limit = 50
    offset = (data['page']-1)*50
    print(f"limit {limit} offset {offset}")
    total_records = 0

    query_result = db.engine.execute(text(
        "SELECT COUNT(*) FROM STOCK WHERE LOWER(SUBSTR(NAME,1,:len)) = LOWER(:name)"), {'name': name, 'len': len(name)})
    for row in query_result:
        total_records = row[0]

    result = db.engine.execute(
        text("SELECT * FROM STOCK WHERE LOWER(SUBSTR(NAME,1,:len)) = LOWER(:name) LIMIT :limit OFFSET :offset").execution_options(autocommit=True), {'name': name, 'len': len(name), 'limit': limit, 'offset': offset})

    stock_response_array = []
    for row in result:
        data = {"id": row[0], "name": row[1],
                "symbol": row[2], "industry": row[3]}
        user_stock = UserStock.query.filter_by(
            user_id=current_user.user_id, stock_id=row[0]).first()

        if(user_stock is not None):
            data["subscribed"] = True
        else:
            data["subscribed"] = False
        stock_response_array.append(data)
    return jsonify({"success": "Stock list fetched", "total_records": total_records, "stockList": stock_response_array})


@app.route("/subscribeStocks", methods=["POST"])
@token_required
def subscribe_stocks(current_user):
    data = request.get_json()
    stocks_to_unsubscribe = None
    stocks_to_subscribe = None

    try:
        stocks_to_subscribe = data['stocks_to_subscribe']
        stocks_to_unsubscribe = data['stocks_to_unsubscribe']
    except:
        return jsonify({"status": "error", "message": "Required Fields are Missing ! Please check and try again"})

    for stock in stocks_to_unsubscribe:
        stock_id = stock
        user_stock = UserStock.query.filter_by(
            stock_id=stock_id, user_id=current_user.user_id).first()

        if(user_stock is not None):
            db.session.delete(user_stock)
            db.session.commit()

    for stock in stocks_to_subscribe:
        stock_id = stock
        user_stock = UserStock.query.filter_by(
            stock_id=stock_id, user_id=current_user.user_id)
        # If User is not subscribed to that stock

        if(user_stock.count() == 0):
            new_user_stock = UserStock(
                stock_id=stock_id, user_id=current_user.user_id)
            print(
                f"Adding stock {stock_id} for user {current_user.user_id}")
            db.session.add(new_user_stock)
            db.session.commit()

    return {"status": "success", "message": "Subscriptions made successfully"}


@app.route("/getSubscribedStocks/<page>")
@token_required
def get_subscribed_stocks(current_user, page):
    user_id = current_user.user_id

    page = int(page)
    limit = 50*page
    offset = limit-50

    result = db.engine.execute(text(
        "SELECT US.STOCK_ID, NAME , SYMBOL , INDUSTRY FROM USERSTOCK US, STOCK ST WHERE US.STOCK_ID == ST.STOCK_ID LIMIT :limit OFFSET :offset").execution_options(autocommit=True), {'limit': limit, 'offset': offset})

    subscribed_stocks = []

    for row in result:
        stock = {}
        stock['id'] = row[0]
        stock['name'] = row[1]
        stock['symbol'] = row[2]
        stock['industry'] = row[3]
        subscribed_stocks.append(stock)
    return jsonify({"success": "List Fetched Successfully", "stock_list": subscribed_stocks})


if __name__ == "__main__":
    app.run(debug=True)
