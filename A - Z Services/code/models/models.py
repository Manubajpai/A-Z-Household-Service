from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Customer(db.Model , UserMixin):
    id = db.Column(db.Integer , primary_key = True)
    email = db.Column(db.String(255) , unique = True , nullable = False)
    password = db.Column(db.String(255) , nullable = False)
    name = db.Column(db.String(100) , nullable = False)
    address = db.Column(db.String(255))
    pincode = db.Column(db.String(10))
    role = db.Column(db.String(50) , default = 'customer')

    def __repr__(self):
        return f"Customer('{self.email}' , '{self.name}')"
    

class Professional(db.Model , UserMixin):
    id = db.Column(db.Integer , primary_key = True)
    email = db.Column(db.String(255) , unique = True , nullable = False)
    password = db.Column(db.String(255) , nullable = False)
    name = db.Column(db.String(100) , nullable = False)
    service_name = db.Column(db.String(150) , nullable = False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    experience = db.Column(db.Integer)
    document = db.Column(db.LargeBinary)
    address = db.Column(db.String(255))
    pincode = db.Column(db.String(10))
    phone_no = db.Column(db.String(15) , nullable = False , unique = True)
    status = db.Column(db.String(20) , default='Pending') # approval status
    role = db.Column(db.String(50) , default = 'professional')

    service = db.relationship('Service', backref=db.backref('professionals', lazy=True))

    def __repr__(self):
        return f"Professional('{self.email}' , '{self.name}')"
    
    
class Service(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    name = db.Column(db.String(100) , nullable = False)
    description = db.Column(db.Text , nullable = False)
    base_price = db.Column(db.Float , nullable = False)


class ServiceRequest(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    service_id = db.Column(db.Integer , db.ForeignKey('service.id') , nullable = False)
    customer_id = db.Column(db.Integer , db.ForeignKey('customer.id') , nullable = False)
    professional_id = db.Column(db.Integer , db.ForeignKey('professional.id'))
    requested_date = db.Column(db.DateTime , default = datetime.utcnow)
    status = db.Column(db.String(20) , default = 'Requested')
    remarks = db.Column(db.Text)

    service = db.relationship('Service' , backref=db.backref('requests' , lazy=True))
    customer = db.relationship('Customer' , backref=db.backref('requests' , lazy=True))
    professional = db.relationship('Professional' , backref=db.backref('assignments' , lazy=True))


class Job(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    service_id = db.Column(db.Integer , db.ForeignKey('service.id'), nullable = False)

    service = db.relationship('Service' , backref = db.backref('jobs' , lazy=True))
    

