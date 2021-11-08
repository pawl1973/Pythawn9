import os

from flask import Flask
from flask_restful import Api, Resource,reqparse
from flask_jwt import JWT,jwt_required
from flask_sqlalchemy import SQLAlchemy

# uri = os.getenv("DATABASE_URL")  # or other relevant config var
# if uri.startswith("postgres://"):
#     uri = uri.replace("postgres://", "postgresql://", 1)
uri='postgresql://eyofazopnldnxe:fae394e67221fa3f8b54595d931344c650d6aec8a9a8ed824ffbae901f12c247@ec2-3-219-154-115.compute-1.amazonaws.com:5432/dab9rp0ap4erui'
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\pama\\PycharmProjects\\pythonProject\\API8\\data.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(uri,r'sqlite:///C:\Users\pmana\PycharmProjects\pythonProject\API9\data.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key='abc'

api = Api(app)
db = SQLAlchemy()

db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

class UserModel(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key= True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))


    def __init__(self,  username, password):
        self.username = username
        self.password = password

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()


    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()


class ItemModel(db.Model):

    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    price = db.Column(db.Float(precision=2))
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'))

    store = db.relationship('StoreModel')

    def __init__(self, name, price, store_id):
        self.name = name
        self.price = price
        self.store_id = store_id

    def json(self):
        return {'name': self.name, 'price': self.price}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

class StoreModel(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))

    items = db.relationship('ItemModel', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def json(self):
        return {'name': self.name, 'items': [item.json() for item in self.items.all()]}

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name= name).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

def authenticate(username, password):
    user = UserModel.find_by_username(username)
    if user and user.password == password:
        return user

def identity(payload):
    user_id= payload['identity']
    return UserModel.find_by_id(user_id)

jwt = JWT(app, authenticate, identity) # /auth

class Item(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('price',
                        type=float,
                        required=True,
                        help='This field cannot be left blank!')
    parser.add_argument('store_id',
                        type=int,
                        required=True,
                        help='Every item needs a store id')

    @jwt_required()
    def get(self, name):
        item = ItemModel.find_by_name(name)
        if item:
            return item.json()
        return {'message': 'Item not found'}, 404

    def post(self, name):
        if ItemModel.find_by_name(name):
            return {'message': "An item with name '{}' already exists.".format(name)}, 400

        data = Item.parser.parse_args()
        item = ItemModel(name, **data)

        try:
            item.save_to_db()
        except:
            return {'message': 'An error occurred inserting the item'}, 500  #internal server error

        return item.json(), 201

    def put(self, name):
        data = Item.parser.parse_args()

        item = ItemModel.find_by_name(name)

        if item is None:
            item = ItemModel(name, **data)
        else:
            item.price = data['price']
            item.store_id = data['store_id']

        item.save_to_db()

        return item.json()

    def delete(self, name):
        item = ItemModel.find_by_name(name)
        if item:
            item.delete_from_db()

        return {'message':'item deleted'}


class ItemList(Resource):
    def get(self):
        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()
        #
        # query = "SELECT * FROM items"
        # result = cursor.execute(query)
        # items = []
        # for row in result:
        #     items.append({'name': row[0], 'price': row[1]})
        #
        # connection.close()

        return {'items': [item.json() for item in ItemModel.query.all()]}


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
                        type=str,
                        required=True,
                        help='This field cannot be left blank!')
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help='This field cannot be left blank!')


    def post(self):
        data = UserRegister.parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {'message': 'A user with that username already exists'}, 400

        user = UserModel(**data)
        user.save_to_db()

        # connection = sqlite3.connect('data.db')
        # cursor = connection.cursor()
        #
        # query = "INSERT INTO users VALUES(NULL, ?, ?)"
        # cursor.execute(query, (data['username'], data['password'],))
        #
        # connection.commit()
        # connection.close()

        return {'Message': 'User created successfully'}, 201

class Store(Resource):
    def get(self, name):
        store = StoreModel.find_by_name(name)
        if store:
            return store.json()
        return {'message': ' Store not found'}, 404

    def post(self, name):
        if StoreModel.find_by_name(name):
            return {'message': "A store with name '{}' already exists".format(name)}, 400
        store = StoreModel(name)
        try:
            store.save_to_db()
        except:
            return {'message': 'There was an error creating the store'}, 500

        return store.json(), 201

    def delete(self, name):
        store = StoreModel.find_by_name(name)
        if store:
            store.delete_from_db()

        return {'message': 'Store deleted'}


class StoreList(Resource):
    def get(self):
        return {'stores': [store.json() for store in StoreModel.query.all()]}


api.add_resource(Store, '/store/<string:name>')
api.add_resource(StoreList, '/stores')
api.add_resource(Item, '/item/<string:name>')
api.add_resource(ItemList, '/items')
api.add_resource(UserRegister, '/register')

if __name__ =='__main__':
    db.init_app(app)
    app.run(port=5000, debug=True)
