from flask import Flask , render_template , request , redirect , url_for , flash , session , jsonify
from flask_login import UserMixin , LoginManager , login_user , login_required , logout_user , current_user
from models.models import db , Customer , Professional , Service , ServiceRequest 
from werkzeug.security import generate_password_hash , check_password_hash 
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



# Ensure 'uploads' directory exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')


# app and database config
app = Flask(__name__)
app.config['SECRET_KEY'] = '94&8M}np;s>WT[d!jH:V0(E}ZlfPnK'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:manubajpai%40123@127.0.0.1:3306/services'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db.init_app(app)


# flask-login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if user_id == "0": # assuming admin has ID as 0
        return AdminUser(id=0 , email='bajpaimanu.99@gmail.com')
    user_type = session.get('user_type')
    if user_type == 'professional':
        return Professional.query.get(int(user_id))
    elif user_type == 'customer':
        return Customer.query.get(int(user_id))
    return None


# setting sending email part
def send_email(to_email , subject , body):
    # email configurations
    sender_email = "azhouseholdservices@gmail.com"
    sender_password = "azhouseholdservices@123"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body , 'plain'))

    try:
        with smtplib.SMTP(smtp_server , smtp_port) as server:
            server.starttls()
            server.login(sender_email , sender_password)
            server.sendmail(sender_email , to_email , message.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")

    
# routes for customer signup
@app.route("/signup_customer" , methods = ['GET' , 'POST'])
def signup_customer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        existing_user = Customer.query.filter_by(email = email).first()
        if existing_user:
            flash('An account with that email already exists as a customer' , 'warning')
            return redirect(url_for('signup_customer'))
        
        new_customer = Customer(email=email , name=name , address=address , pincode=pincode)
        new_customer.password = generate_password_hash(password)

        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('signup_customer.html')


# route for professional signup
@app.route("/signup_professional" , methods = ['GET' , 'POST'])
def signup_professional():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        service_name = request.form['service_name']
        experience = request.form.get('experience')
        if experience:
            experience = int(experience)
        else:
            experience = 0

        document = request.files.get('document')
        # handle the document 
        if document:
            filename = secure_filename(document.filename)
            file_path = os.path.join('uploads' , filename)
            document.save(file_path)
        else:
            flash('No document uploaded.' , 'warning')   

        address = request.form.get('address')
        phone_no = request.form.get('phone_no')
        pincode = request.form.get('pincode')
        existing_user = Professional.query.filter_by(email=email).first()

        if existing_user:
            flash('An account with that email already exists as a professional.' , 'warning')
            return redirect(url_for('signup_professional'))
        

        new_professional = Professional(email=email , name=name , service_name=service_name , experience=experience , address=address , pincode=pincode , phone_no=phone_no)
        new_professional.password = generate_password_hash(password)

        db.session.add(new_professional)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template('signup_professional.html')


class AdminUser(UserMixin):
    def __init__(self,id,email):
        self.id = id
        self.email = email


# login route for customer , professional and admin
@app.route('/login' , methods = ['GET' , 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # hardcoding the email and password
        admin_email = 'bajpaimanu.99@gmail.com'
        admin_password = 'ManuB#123'

        if email == admin_email and password == admin_password:
            admin_user = AdminUser(id=0 , email=admin_email)
            login_user(admin_user)
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        user = Professional.query.filter_by(email=email).first() or Customer.query.filter_by(email=email).first()

        if user and check_password_hash(user.password , password):
            login_user(user)
            session['user_type'] = 'professional' if isinstance(user , Professional) else 'customer'
            if user.role == 'professional':
                return redirect(url_for('professional_dashboard'))
            elif user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password.' , 'danger')
            return redirect(url_for('login'))
        
    return render_template('login.html')


# logout route 
@app.route('/logout')
@login_required
def logout():
    session.pop('admin' , None) # remove the admin session if present
    logout_user()
    session.clear()
    return redirect(url_for('login'))


# route for admin dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session.get('admin'):
        # retrieve all data from database
        services = Service.query.all()
        professionals = Professional.query.all()
        customers = Customer.query.all()
        service_requests = ServiceRequest.query.all()

        return render_template('admin_dashboard.html' , services=services , professionals=professionals , customers=customers ,  service_requests=service_requests )
    else:
        return redirect(url_for('login'))


# routes for customer dashboard
@app.route('/customer_dashboard' , methods = ['GET'])
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('logout'))
    
    services = Service.query.all()
    unique_services = {service.name: service for service in services}.values()
    service_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).all()
    return render_template('customer_dashboard.html' , services=unique_services , service_requests = service_requests)


@app.route('/get_jobs/<int:service_id>' , methods = ['GET'])
@login_required
def get_jobs(service_id):
    service = Service.query.get_or_404(service_id)
    related_services = Service.query.filter_by(name=service.name).all()
    jobs_data = [
        {
            'id': related_service.id,
            'name':related_service.name,
            'description': related_service.description,
            'base_price': related_service.base_price
        } for related_service in related_services
    ]
    return jsonify(jobs_data)


@app.route('/book_job/<int:service_id>' , methods = ['POST'])
@login_required
def book_job(service_id):
    existing_request = ServiceRequest.query.filter_by(service_id=service_id , customer_id=current_user.id).first()
    if existing_request:
        return jsonify({"error": "You have already booked this service!" }), 400
                        
    new_request = ServiceRequest(
        service_id = service_id,
        customer_id = current_user.id,
        status = 'Requested'
    )
    db.session.add(new_request)
    db.session.commit()

    service = Service.query.get_or_404(service_id)
    available_professionals = Professional.query.filter_by(service_name=service.name , status = "Approved").all()

    if not available_professionals:
        return jsonify({
            "id": new_request.id,
            "service_name": new_request.service.name,
            "status": new_request.status
        }), 201

    return jsonify({
        "id": new_request.id,
        "service_name": new_request.service.name,
        "status": new_request.status
    }), 201


@app.route('/customer_remarks/<int:request_id>' , methods = ['GET' , 'POST'])
@login_required
def customer_remarks(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        rating = request.form['service_rating']
        remarks = request.form['service_remarks']

        service_request.remarks = remarks
        service_request.status = 'Closed'
        db.session.commit()

        return redirect(url_for('customer_dashboard'))
    return render_template('customer_remarks.html' , service_request = service_request)


@app.route('/customer_profile' , methods = ['GET' , 'POST'])
@login_required
def customer_profile():
    customer = Customer.query.get_or_404(current_user.id)

    if request.method == 'POST':
        customer.name = request.form.get('name' , customer.name)
        customer.email = request.form.get('email' , customer.email)
        customer.address = request.form.get('address' , customer.email)
        customer.pincode = request.form.get('pincode' , customer.pincode)
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password or new_password or confirm_password:
            if not check_password_hash(customer.password , current_password):
                flash('Current password is incorrect' , 'danger')
                return render_template('Customer_profile.html' , customer=customer)
            
            if new_password != confirm_password:
                flash('New passwords do not match' , 'danger')
                return render_template('Customer_profile.html' , customer=customer)
            
            customer.password = generate_password_hash(new_password)
            
            
        db.session.commit()
        return redirect(url_for('customer_profile'))
    
    return render_template('Customer_profile.html' , customer=customer)


@app.route('/customer_summary' , methods=['GET'])
@login_required
def customer_summary():
    return render_template('customer_summary.html')


@app.route('/customer_summary/data' , methods = ['GET'])
@login_required
def customer_summary_data():
    customer_id = current_user.id
    requested_count = ServiceRequest.query.filter_by(customer_id=customer_id , status='Requested').count()
    closed_count = ServiceRequest.query.filter_by(customer_id=customer_id , status='Closed').count()
    active_count = ServiceRequest.query.filter_by(customer_id=customer_id , status='Active').count()

    return jsonify({
        'requested': requested_count,
        'closed': closed_count,
        'active': active_count
    })


@app.route('/customer_search' , methods = ['GET' , 'POST'] )
@login_required
def customer_search():
    services = []
    professionals = []

    if request.method == 'POST':
        search_query = request.form['search_query'].strip().lower()
        services = Service.query.filter(Service.name.ilike(f'%{search_query}')).all()
        professionals = Professional.query.filter(Professional.service_name.ilike(f'%{search_query}')).all()

    return render_template('customer_search.html' , services = services , professionals=professionals)
        

# routes for professional dash
@app.route('/professional_dashboard' , methods = ['GET' , 'POST'])
@login_required
def professional_dashboard():
    if current_user.role != 'professional':
        return redirect(url_for('login'))
    
    service_requests = ServiceRequest.query.join(Service).filter(Service.name == current_user.service_name , ServiceRequest.status == 'Requested')
    closed_requests = ServiceRequest.query.filter_by(professional_id = current_user.id , status='Closed').all()

    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action')

        service_request = ServiceRequest.query.get_or_404(request_id)
        if action == 'accept':
            service_request.status = 'Active'
            service_request.professional_id = current_user.id
            
        elif action == 'reject':
            service_request.status = 'Rejected'
            service_request.professional_id = current_user.id
            

        db.session.commit()
        return redirect(url_for('professional_dashboard'))
    return render_template('professional_dashboard.html' , service_requests=service_requests , closed_requests=closed_requests)


@app.route('/professional_profile' , methods = ['GET' , 'POST'])
@login_required
def professional_profile():
    professional = Professional.query.get_or_404(current_user.id)

    if request.method == 'POST':
        professional.name = request.form.get('name' , professional.name)
        professional.email = request.form.get('email' , professional.email)
        professional.service_name = request.form.get('service_name' , professional.service_name)
        professional.experience = request.form.get('experience' , professional.experience)
        professional.address = request.form.get('address' , professional.address)
        professional.pincode = request.form.get('pincode' , professional.pincode)
        professional.phone_no = request.form.get('phone_no' , professional.phone_no)

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password or new_password or confirm_password:
            if not check_password_hash(professional.password , current_password):
                flash('Current password is incorrect' , 'danger')
                return render_template('professional_profile.html' , professional=professional)
            
            if new_password != confirm_password:
                flash('New passwords do not match' , 'danger')
                return render_template('professional_profile.html' , professional=professional)
            
            professional.password = generate_password_hash(new_password)
            
            
        db.session.commit()
        
        return redirect(url_for('professional_profile'))

    return render_template('professional_profile.html' , professional=professional)


@app.route('/professional_summary' , methods = ['GET' , 'POST'])
@login_required
def professional_summary():
    return render_template('professional_summary.html')


@app.route('/professional_summary/data' , methods = ['GET'])
@login_required
def professional_summary_data():
    professional_id = current_user.id
    closed_count = ServiceRequest.query.filter_by(professional_id=professional_id , status='Closed').count()
    active_count = ServiceRequest.query.filter_by(professional_id=professional_id , status='Active').count()
    rejected_count = ServiceRequest.query.filter_by(professional_id=professional_id , status='Rejected').count()

    return jsonify({
        'closed': closed_count,
        'active': active_count,
        'rejected': rejected_count
    })


@app.route('/professional_search' , methods = ['GET' , 'POST'])
@login_required
def professional_search():
    professional = Professional.query.filter_by(id=current_user.id).first()
    service_requests = ServiceRequest.query.join(Service).join(Customer).filter(
        ServiceRequest.status == 'Requested',
        Service.name == professional.service_name
    ).all()

    return render_template('professional_search.html' , service_requests=service_requests)


@app.route('/accept_service_request/<int:request_id>', methods=['POST'])
@login_required
def accept_service_request(request_id):
    
    service_request = ServiceRequest.query.get(request_id)
    if service_request:
        service_request.status = 'Active'
        service_request.professional_id = current_user.id
        db.session.commit()
    return redirect(url_for('professional_search'))


@app.route('/reject_service_request/<int:request_id>', methods=['POST'])
@login_required
def reject_service_request(request_id):

    service_request = ServiceRequest.query.get(request_id)
    if service_request:
        service_request.status = 'Rejected'
        service_request.professional_id = current_user.id
        db.session.commit()
    return redirect(url_for('professional_search'))


# route for home page
@app.route("/")
def home():
    return render_template('home.html')


# all routes of service section
@app.route('/create_service' , methods=['GET' , 'POST'])
def create_service():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        base_price = request.form['base_price']

        new_service = Service(name=name , description=description , base_price=base_price)
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('create_service.html')


@app.route('/edit_service/<int:service_id>' , methods=['POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.name = request.form['name']
    service.description = request.form['description']
    service.base_price = request.form['base_price']
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_service/<int:service_id>' , methods=['POST'])
@login_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# all routes of professional section
@app.route('/approve_professional/<int:professional_id>' , methods=['POST'])
@login_required
def approve_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.status = 'Approved'
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/reject_professional/<int:professional_id>' , methods=['POST'])
@login_required
def reject_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    professional.status = 'Rejected'
    db.session.commit()
    send_email(professional.email ,"Your application status" , "We regret to inform you that your application has been rejected.")
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_professional/<int:professional_id>' , methods=['POST'])
@login_required
def delete_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    db.session.delete(professional)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# route for admin summary
@app.route('/admin_summary')
def admin_summary():
    # chart 1
    services_count = (
        Service.query.with_entities(Service.name , db.func.count(Service.id))
        .group_by(Service.name)
        .all()
    )
    services_data = [{"name":name or "Unknown" , "count":count} for name , count in services_count]
              
    # chart 2
    professionals_count = (
        Professional.query.join(Service , Professional.service_name == Service.name)
        .with_entities(Service.name , db.func.count(Professional.id))
        .group_by(Service.name).all()
    )
    
    professionals_data = [{"name":name  , "count":count} for name , count in professionals_count]
    
    # chart 3
    requests_status = (
        ServiceRequest.query.with_entities(ServiceRequest.status , db.func.count(ServiceRequest.id))
        .group_by(ServiceRequest.status).all()
    )
    requests_data = [{"status":status or "Unknown" , "count":count} for status , count in requests_status ]

    return render_template('admin_summary.html' , services_data=services_data , professionals_data=professionals_data, requests_data = requests_data)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
