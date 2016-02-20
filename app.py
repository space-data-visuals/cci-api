#!/usr/bin/env python

from flask import Flask, jsonify, abort, request

from flask.ext.sqlalchemy import SQLAlchemy

from datetime import datetime


# CONFIGURATION #


app = Flask(__name__)

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

date_format = '%Y-%m-%d %H:%M:%S'


# MODELS #


class Experiment(db.Model):
    """Represents an ESA CCI experiment.

    Attributes:
        desc (str): Short description of the experiment.
        id (int): Primary key of the experiment in database.
        name (str): Name of the experiment.
        products: Products related to the experiment.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    desc = db.Column(db.String(1000))
    products = db.relationship('Product', backref='experiment', lazy='dynamic')

    def __init__(self, name, desc):
        self.name = name
        self.desc = desc

    def serialize(self):
        """Returns experiment data in easily serializeable format.

        Returns:
            dict: Dictionary representing the experiment.
        """
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc
        }


class Product(db.Model):
    """Represents an experiment's product.

    Attributes:
        desc (str): Short description of the experiment.
        experiment_id (int): Primary key of the related experiment in database.
        files: Files related to the product.
        id (int): Primary key of the product in database.
        name (str): Name of the product.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    desc = db.Column(db.String(1000))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    files = db.relationship('File', backref='product', lazy='dynamic')

    def __init__(self, name, desc, experiment_id):
        self.name = name
        self.desc = desc
        self.experiment_id = experiment_id

    def serialize(self):
        """Returns product data in easily serializeable format.

        Returns:
            dict: Dictionary representing the product.
        """
        return {
            'id': self.id,
            'name': self.name,
            'desc': self.desc,
            'experiment_id': self.experiment_id
        }


class File(db.Model):
    """Represents a product's file.

    Attributes:
        dateTime: File's creation time.
        id (int): Primary key of the file in database.
        level (str): Data processing level of the file.
        path (str): Path to the file on the ESA CCI FTP server.
        product_id (int): Primary key of the related product in database.
    """
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(1000))
    dateTime = db.Column(db.DateTime)
    level = db.Column(db.String(10))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    def __init__(self, path, dateTime, level, product_id):
        self.path = path
        self.dateTime = datetime.strptime(dateTime, date_format)
        self.level = level
        self.product_id = product_id

    def serialize(self):
        """Returns file data in easily serializeable format.

        Returns:
            dict: Dictionary representing the file.
        """
        return {
            'id': self.id,
            'path': self.path,
            'dateTime': str(self.dateTime),
            'level': self.level,
            'product_id': self.product_id
        }


# ROUTES #


# Experiment related routes


@app.route('/experiments/', methods=['GET'])
def get_experiments():
    exps = Experiment.query.all()
    return jsonify({'experiments': [exp.serialize() for exp in exps]})


@app.route('/experiments/<int:id>', methods=['GET'])
def get_experiment(id):
    return jsonify({'experiment': Experiment.query.get(id).serialize()})


@app.route('/experiments/<int:id>', methods=['PUT'])
def update_experiment(id):
    exp = Experiment.query.get(id)
    exp.name = request.json.get('name', exp.name)
    exp.desc = request.json.get('desc', exp.desc)
    db.session.commit()
    return jsonify({'experiment': exp.serialize()})


@app.route('/experiments/<int:id>', methods=['DELETE'])
def delete_experiment(id):
    db.session.delete(Experiment.query.get(id))
    db.session.commit()
    return jsonify({'result': True})


@app.route('/experiments/', methods=['POST'])
def create_experiment():
    if not request.json or 'name' not in request.json:
        abort(400)
    exp = Experiment(request.json.get('name'), request.json.get('desc', ''))
    db.session.add(exp)
    db.session.commit()
    return jsonify({'experiment': exp.serialize()}), 201


# Product related routes


@app.route('/products/', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify({'products': [prd.serialize() for prd in products]})


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    return jsonify({'product': Product.query.get(id).serialize()})


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    prd = Product.query.get(id)
    prd.name = request.json.get('name', prd.name)
    prd.desc = request.json.get('desc', prd.desc)
    prd.experiment_id = request.json.get('experiment_id', prd.experiment_id)
    db.session.commit()
    return jsonify({'product': prd.serialize()})


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    db.session.delete(Product.query.get(id))
    db.session.commit()
    return jsonify({'result': True})


@app.route('/products/', methods=['POST'])
def create_product():
    if not request.json or 'name' not in request.json \
                        or 'experiment_id' not in request.json:
        abort(400)
    prd = Product(request.json.get('name'), request.json.get('desc', ''),
                  request.json.get('experiment_id'))
    db.session.add(prd)
    db.session.commit()
    return jsonify({'product': prd.serialize()}), 201


# File related routes


@app.route('/files/', methods=['GET'])
def get_files():
    if not request.json:
        files = File.query.all()
    else:
        args = request.json
        s = args['start_date'] if 'start_date' in args \
            else datetime.min.strftime(date_format)
        e = args['end_date'] if 'end_date' in args \
            else datetime.max.strftime(date_format)
        products = []
        if 'product_ids' in args:
            products = Product.query.filter(
                Product.id.in_(args['product_ids'])).all()
        if 'experiment_ids' in args:
            expts = Experiment.query.filter(
                Experiment.id.in_(args['experiment_ids'])).all()
            for expt in expts:
                products = products + expt.products
        file_ids = []
        for p in products:
            for f in p.files:
                file_ids.append(f.id)   # file IDs of selected exp and products
        files = File.query.filter(      # SQL filtering
                    File.id.in_(file_ids),
                    File.dateTime >= s,
                    File.dateTime <= e).all()
    return jsonify({'files': [f.serialize() for f in files]})


@app.route('/files/<int:id>', methods=['GET'])
def get_file(id):
    return jsonify({'file': File.query.get(id).serialize()})


@app.route('/files/<int:id>', methods=['PUT'])
def update_file(id):
    f = File.query.get(id)
    f.path = request.json.get('path', f.path)
    if 'dateTime' in request.json:
        f.dateTime = datetime.strptime(request.json['dateTime'], date_format)
    f.level = request.json.get('level', f.level)
    f.product_id = request.json.get('product_id', f.product_id)
    db.session.commit()
    return jsonify({'file': f.serialize()})


@app.route('/files/<int:id>', methods=['DELETE'])
def delete_file(id):
    db.session.delete(File.query.get(id))
    db.session.commit()
    return jsonify({'result': True})


@app.route('/files/', methods=['POST'])
def create_file():
    if not request.json or 'path' not in request.json \
                        or 'product_id' not in request.json:
        abort(400)
    f = File(request.json.get('path'),
             request.json.get('dateTime', '1900-01-01 00:00:00'),
             request.json.get('level', ''), request.json.get('product_id'))
    db.session.add(f)
    db.session.commit()
    return jsonify({'file': f.serialize()}), 201


# RUN #


db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
