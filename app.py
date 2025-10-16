from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask import render_template, session, redirect, url_for, flash
from flask_mail import Message
from fpdf import FPDF
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'daminmain@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'kpqtxqskedcykwjz'  # Replace with your email password

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    time = db.Column(db.String(50), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    college_name = db.Column(db.String(255), nullable=True)
    event_name = db.Column(db.String(255))  
    status = db.Column(db.String(50), default="Pending")

class Sponsorship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)  

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid Admin Credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    events = Event.query.all()
    bookings = Booking.query.all()
    return render_template('admin_dashboard.html', events=events, bookings=bookings)

@app.route('/logout_admin')
def logout_admin():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add_sponsorship():
    if request.method == 'POST':  # When the form is submitted
        code_name = request.form['code_name']
        department = request.form['department']
        year = request.form['year']
        amount = request.form['amount']
        status = request.form['status']

        new_sponsorship = Sponsorship(
            code_name=code_name, department=department, year=year, amount=amount, status=status
        )
        db.session.add(new_sponsorship)
        db.session.commit()

        flash("Sponsorship Added Successfully!", "success")
        return redirect(url_for('home'))

    # If it's a GET request, show the form
    return render_template('sponsorship.html')

# Add Event
@app.route('/add_event', methods=['POST'])
def add_event():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    event = Event(
        name=request.form['name'],
        date=request.form['date'],
        location=request.form['location'],
        college=request.form['college'],
        venue=request.form['venue'],
        time=request.form['time']
    )
    db.session.add(event)
    db.session.commit()
    flash('Event Added Successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/reschedule_event/<int:event_id>', methods=['GET', 'POST'])
def reschedule_event(event_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    event = Event.query.get_or_404(event_id)  # Fetch event details

    # Fetch student booking details
    booking = Booking.query.filter_by(event_id=event_id).first()
    if booking:
        student = User.query.get(booking.user_id)  # Assuming 'user_id' is a foreign key in the 'Booking' model
    else:
        student = None  # If no booking exists, set to None
    
    if request.method == 'POST':
        event.date = request.form['date']
        event.time = request.form['time']
        event.venue = request.form['venue']
        db.session.commit()
        flash('Event Rescheduled Successfully', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('reschedule_event.html', event=event, student=student)




@app.route('/delete_event/<int:event_id>')
def delete_event(event_id):
    
    event = db.session.get(Event, event_id) 

    if event is None:  # Check if event exists
        flash('Event not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    db.session.delete(event)
    db.session.commit()
    
    flash('Event Deleted Successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/approve_booking/<int:booking_id>')
def approve_booking(booking_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    booking = db.session.get(Booking, booking_id)  

    if booking is None:
        flash('Booking not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    user = db.session.get(User, booking.user_id)  
    if user is None:
        flash('User associated with this booking not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Use the college name from the User model
    college_name = user.college_name if hasattr(user, 'college_name') and user.college_name else "xyz College"

    try:
        # Generate a certificate (Fixed: using user.college_name instead of booking.college_name)
        certificate_path = generate_certificate(user.name, booking.event_name, college_name)

        # Send approval email with certificate
        msg = Message('Event Booking Approved', sender='your_email@gmail.com', recipients=[user.email])
        msg.body = f"Your booking for the event '{booking.event_name}' has been approved!\n\nPlease find your certificate attached."

        with open(certificate_path, 'rb') as cert_file:
            msg.attach(f"{user.name}_certificate.pdf", "application/pdf", cert_file.read())

        mail.send(msg)

        # Delete booking after approval
        db.session.delete(booking)
        db.session.commit()

        # Remove the certificate file after sending
        if os.path.exists(certificate_path):
            os.remove(certificate_path)

        flash('Booking Approved & Certificate Sent via Email', 'success')
    except Exception as e:
        flash(f'Error processing booking: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))


from fpdf import FPDF
import os
from datetime import datetime

def generate_certificate(user_name, event_name, college_name):
    pdf = FPDF('L', 'mm', 'A4')  # Landscape mode
    pdf.add_page()

    # Set Background Color
    pdf.set_fill_color(230, 230, 250)  # Light lavender background
    pdf.rect(0, 0, 297, 210, style='F')  # Filling the entire page

    # Add Border
    pdf.set_line_width(2)
    pdf.rect(10, 10, 277, 190)  # Create a border

    # Certificate Title
    pdf.set_font("Arial", style='B', size=28)
    pdf.set_text_color(0, 102, 204)  # Blue Color
    pdf.cell(0, 30, "Certificate of Participation", ln=True, align='C')

    pdf.ln(5)  # Space

    # Certificate ID
    certificate_id = f"ID-{int(datetime.now().timestamp())}"  # Unique ID
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(100, 100, 100)  # Gray Color
    pdf.cell(0, 10, f"Certificate No: {certificate_id}", ln=True, align='R')

    pdf.ln(10)  # Space

    # Body Text
    pdf.set_font("Arial", size=16)
    pdf.set_text_color(0, 0, 0)  # Black color
    pdf.cell(0, 10, "This is to certify that", ln=True, align='C')

    # User Name (Highlighted)
    pdf.set_font("Arial", style='B', size=22)
    pdf.set_text_color(255, 0, 0)  # Red Color
    pdf.cell(0, 10, user_name, ln=True, align='C')

    # Event Name
    pdf.set_font("Arial", size=16)
    pdf.set_text_color(0, 0, 0)  # Black
    pdf.cell(0, 10, "has successfully participated in", ln=True, align='C')

    pdf.set_font("Arial", style='B', size=18)
    pdf.set_text_color(0, 102, 204)  # Blue
    pdf.cell(0, 10, event_name, ln=True, align='C')

    # Organizing College Name
    pdf.ln(5)  # Space
    pdf.set_font("Arial", size=16)
    pdf.set_text_color(0, 0, 0)  # Black
    pdf.cell(0, 10, f"Organized by {college_name}", ln=True, align='C')

    pdf.ln(10)  # Space

    # Appreciation Text
    pdf.set_font("Arial", size=14)
    pdf.set_text_color(50, 50, 50)  # Dark Gray
    pdf.multi_cell(0, 8, "We appreciate your dedication and effort in making this event a success. "
                         "Your enthusiasm and commitment have made a significant impact.", align='C')

    pdf.ln(10)  # Space

    # Date & Signature
    current_date = datetime.today().strftime('%Y-%m-%d')  
    pdf.set_font("Arial", size=14)
    pdf.set_text_color(0, 0, 0)  
    pdf.cell(0, 10, f"Date: {current_date}", ln=True, align='L')

    pdf.ln(15)  # Space before signature lines

    # Adding Signature Images
    sign2_path = "sign2.jpg"

    if os.path.exists(sign2_path):
        pdf.image(sign2_path, x=210, y=160, w=50, h=20)
    else:
        pdf.cell(0, 10, "____________________", ln=1, align='R')

    pdf.ln(15)  # Space

    # Placeholder for an official seal
    pdf.set_font("Arial", style='B', size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "(Official Seal Here)", ln=True, align='C')

    # Save the certificate
    os.makedirs("certificates", exist_ok=True)  # Ensure folder exists
    certificate_path = f"certificates/{user_name}_certificate.pdf"
    pdf.output(certificate_path)

    return certificate_path


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration Successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials', 'danger')
    return render_template('login.html')

from datetime import datetime, date


from datetime import datetime, date
from flask import render_template
from flask_login import login_required, current_user

@app.route('/dashboard')
@login_required
def dashboard():
    current_date = date.today()

    events = Event.query.all()
    
    # Ensure all event dates are converted to datetime.date
    for event in events:
        if isinstance(event.date, str):
            try:
                event.date = datetime.strptime(event.date, "%Y-%m-%d").date()
            except ValueError:
                try:
                    event.date = datetime.strptime(event.date, "%d/%m/%Y").date()
                except ValueError:
                    print(f"Skipping invalid date format: {event.date}")
                    event.date = current_date  # Assign a fallback to prevent errors

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard.html', 
                           events=events, 
                           bookings=bookings, 
                           current_date=current_date)


@app.route('/book_event/<int:event_id>')
def book_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Fetch the current user's college name
    college_name = current_user.college_name if hasattr(current_user, 'college_name') else " "

    # Create a booking with college name
    booking = Booking(user_id=current_user.id, event_id=event.id, event_name=event.name, college_name=college_name)
    
    db.session.add(booking)
    db.session.commit()
    
    flash("Event booked successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
