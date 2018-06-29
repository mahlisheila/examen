import os
from datetime import datetime
from dateutil import parser as datetime_parser
from dateutil.tz import tzutc
from flask import Flask, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from utils import split_url


basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, '../data.sqlite')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

db = SQLAlchemy(app)

class ValidationError(ValueError):
    pass


class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), index=True)
    pedidos = db.relationship('Pedido', backref='cliente', lazy='dynamic') #<---- relationship 

    def get_url(self):
        """
        Retonar el url del cliente, representado en formato json
        """
        return url_for('get_cliente', id=self.id, _external=True)


    def export_data(self):
        """
        genera información representado en formato json, del objeto cliente
        """


        return {
            'self_url': self.get_url(),
            'nombre': self.nombre,
            'pedidos_url': url_for('get_pedidos_cliente', id=self.id, _external=True)
        }

    def import_data(self, data):
        """
        crea el nuevo recurso cliente, representado en formato json
        """
        try:
            self.nombre = data['nombre']
        except KeyError as e:
            raise ValidationError('Cliente no valido: ausente ...... ' + e.args[0])
        return self

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), index=True)
    items = db.relationship('Item', backref='producto', lazy='dynamic')

    def get_url(self):
        return url_for('get_producto', id=self.id, _external=True)

    def export_data(self):
        return {
            'self_url': self.get_url(),
            'nombre': self.nombre
            }

    def import_data(self, data):
        try:
            self.nombre = data['nombre']
        except KeyError as e:
            raise ValidationError('Producto no valido: perdido' + e.args[0])
        return self

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), index=True)
    fecha = db.Column(db.DateTime, default=datetime.now)
    items = db.relationship('Item', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')

    def get_url(self):
        return url_for('get_pedido', id=self.id, _external=True)

    def export_data(self):
        return {
            'self_url': self.get_url(),
            'cliente_url': self.cliente.get_url(),
            'fecha': self.fecha.isoformat()+'Z',
            'items_url': url_for('get_pedido_items', id=self.id, _external=True)
        }

    def import_data(self, data):
        try:
            self.fecha = datetime_parser.parse(data['fecha']).astimezone(tzutc()).replace(tzinfo=None)
        except KeyError as e:
            raise ValidationError('Pedido no valido: perdido' + e.args[0])
        return self

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), index=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), index=True)
    cantidad = db.Column(db.Integer)

    def get_url(self):
        return url_for('get_item', id=self.id, _external=True)

    def export_data(serlf):
        return {
            'self_url': self.get_url(),
            'pedido_url': self.pedido.get_url(),
            'producto_url': self.producto.get_url(),
            'cantidad': self.cantidad
        }

    def import_data(self, data):
        try:
            self.cantidad = data['cantidad']
        except KeyError as e:
            raise ValidationError('Cliente no valido: ausente ...... ' + e.args[0])
        return self

# modulos de rutas
# ----CLIENTES

@app.route('/clientes/', methods=['GET'])
def get_clientes():
    """
    Función que obtiene la lista de clienes, con contenido obtenido por listas por comprensión
    """
    #print('-------------')
    #for cliente in Cliente.query.all():
    #    print(cliente.get_url())
    #print('-------------')

    return jsonify({'clientes': [cliente.get_url() for cliente in
                                 Cliente.query.all()]})

@app.route('/clientes/', methods=['POST'])
def new_cliente():
    """
    Función que crea un cliente
    """
    cliente = Cliente()
    print(".....request.json......")
    print(request.json)
    print(request)
    print(".....request.json......")
    
    cliente.import_data(request.json)
    db.session.add(cliente)
    db.session.commit()
    return jsonify({}), 201, {'Localizacion': cliente.get_url()}

@app.route('/clientes/<int:id>', methods=['GET'])
def get_cliente(id):
    """
    Lista individualmente a los clientes
    print("solo conslta %s" % Cliente.query.get_or_404(id).export_data())
    print("en formato json: ")
    print (jsonify(Cliente.query.get_or_404(id).export_data()))
    """ 
    return jsonify(Cliente.query.get_or_404(id).export_data())

@app.route('/clientes/<int:id>', methods=['PUT'])
def edit_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    cliente.import_data(request.json)
    db.session.add(cliente)
    db.session.commit()
    return jsonify({})

@app.route('/eliminar/<id>', methods=['DELETE'])
def rm_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({})

# ----- PRODUCTOS
@app.route('/productos/', methods=['GET'])
def get_productos():
    print("entro aqui!!!")
    return jsonify({'productos': [producto.get_url() for producto in Producto.query.all()]})

@app.route('/productos/<int:id>', methods=['GET'])
def get_producto(id):
    return jsonify(Producto.query.get_or_404(id).export_data())

@app.route('/productos/', methods=['POST'])
def nuevo_producto():
    producto = Producto()
    producto.import_data(request.json)
    db.session.add(producto)
    db.session.commit()
    return jsonify({}), 201, {'Localizacion': producto.get_url()}

@app.route('/productos/<int:id>', methods=['PUT'])
def edit_producto(id):
    producto = Producto.query.get_or_404(id)
    producto.import_data(request.json)
    db.session.add(producto)
    db.session.commit()
    return jsonify({})

#---- PEDIDOS
@app.route('/pedidos/', methods=['GET'])
def get_pedidos():
    return jsonify({'pedidos': [pedido.get_url() for pedido in Pedido.query.all()]})

@app.route('/clientes/<int:id>/pedidos/', methods=['GET'])
def get_pedidos_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    return jsonify({'pedidos': [pedido.get_url() for pedido in Pedido.query.all()]})

@app.route('/pedidos/<int:id>', methods=['GET'])
def get_pedido(id):
    return jsonify(Pedido.query.get_or_404(id).export_data())

@app.route('/clientes/<int:id>/pedidos/', methods=['POST'])
def nuevo_pedido_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    pedido = Pedido(cliente=cliente)
    pedido.import_data(request.json)
    db.session.add(pedido)
    db.session.commit()
    return jsonify({}), 201, {'Localizacion': pedido.get_url()}

@app.route('/pedidos/<int_id>', methods=['DELETE'])
def delete_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    db.session.delete(pedido)
    db.session.commit()
    return jsonify({})

@app.route('/pedidos/<int:id>', methods=['PUT'])
def edit_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    pedido.import_data(request.json)
    db.session.add(pedido)
    db.session.commit()
    return jsonify({})

#---ITEMS
@app.route('/pedidos/<int:id>/items/', methods=['GET'])
def get_pedido_items(id):
    pedido = Pedido.query.get_or_404(id)
    return jsonify({'items': [item.get_url() for item in pedido.items.all()]})

@app.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    return jsonify(Item.query.get_or_404(id).export_data())

@app.route('/pedidos/<int:id>/items/', methods=['POST'])
def nuevo_item_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    item = Item(pedido=pedido)
    item.import_data(request.json)
    db.session.add(item)
    db.session.commit()
    return jsonify({}), 201, {'Localización': item.get_url()}

@app.route('/items/<int:id>', methods=['PUT'])
def editar_item(id):
    items = Item.query.get_or_404(id)
    items.import_data(request.json)
    db.session.add(item)
    db.session.commit()
    return jsonify({})
    

@app.route('/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
