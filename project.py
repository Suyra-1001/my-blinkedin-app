import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'blinkedin_ultimate_cyber_2026'
import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
+ os.path.join(basedir,'blinkedin_ultra.db')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")
with app.app_context():
    db.create_all()
    print("Database Tables Created Successfully!")
# --- 90+ PROFESSIONS ---
PROFESSIONS = sorted(["Electrician", "Plumber", "AC Repair", "Home Cleaner", "Carpenter", "Painter", "Pest Control", "Appliance Repair", "Gardener", "Yoga Trainer", "Math Tutor", "Physics Tutor", "Guitar Teacher", "Makeup Artist", "Hair Stylist", "Massage for Men", "Car Washer", "Mechanic", "Pet Groomer", "Dog Walker", "Delivery Partner", "Bike Taxi", "Packers & Movers", "Chef at Home", "Tailor", "Dry Cleaning", "Interior Designer", "Event Planner", "Security Guard", "Physiotherapist", "Laptop Repair", "Mobile Repair", "Roofer", "Locksmith", "CCTV Installer", "Solar Panel Tech", "Tattoo Artist", "Dance Teacher", "Zumba Instructor", "Nutritionist", "Web Developer", "App Developer", "SEO Expert", "Graphic Designer", "Video Editor", "Chartered Accountant", "Lawyer", "Astrologer", "Pandit Ji", "Vaastu Consultant", "Car Driver", "Baby Sitter", "Elderly Care", "Nurse at Home", "Wall Paper Expert", "Chimney Repair", "RO Service", "Microwave Repair", "Inverter Repair", "Mason (Mistry)", "Tile Layer", "False Ceiling Expert", "Aluminium Work", "Welder", "Glass Cutter", "Event Decorator", "DJ for Party", "Bouncer", "Bodyguard", "Private Tutor", "Foreign Language Teacher", "IELTS Trainer", "Piano Teacher", "Drum Instructor", "Social Media Manager", "Tax Consultant", "Notary Service", "VFX Artist", "UI/UX Designer", "Network Engineer", "Data Recovery Expert", "Key Maker"])

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20)) 
    profession = db.Column(db.String(100))
    city = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    phone = db.Column(db.String(15))
    wallet = db.Column(db.Integer, default=1000)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)
    customer_name = db.Column(db.String(100))
    service_needed = db.Column(db.String(100))
    pickup_address = db.Column(db.Text)
    drop_address = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending') 
    pro_id = db.Column(db.Integer, nullable=True)
    amount = db.Column(db.Integer, default=0)
    payment_mode = db.Column(db.String(20), default='Cash')
    cust_lat = db.Column(db.Float)
    cust_lng = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    rating = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    sender_id = db.Column(db.Integer)
    sender_name = db.Column(db.String(100))
    content = db.Column(db.Text)
    msg_type = db.Column(db.String(20), default='text') # text, photo, audio
    file_path = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# --- ROUTES ---
@app.route('/')
def index(): 
    return render_template('index.html', professions=PROFESSIONS)
@app.route('/force-admin-access')
def force_admin_access():
    # Ye database ke sabse pehle user ko admin bana dega
    user = User.query.first() 
    if user:
        user.role = 'admin'
        db.session.commit()
        return f"SUCCESS! {user.email} ab Admin ban gaya hai. Ab login karein."
    else:
        return "ERROR: Database khali hai. Pehle signup karein!"

@app.route('/signup', methods=['POST'])
def signup():
    try:
        d = request.form
        pw = bcrypt.generate_password_hash(d.get('password')).decode('utf-8')
        u = User(
            username=d['username'], 
            email=d['email'], 
            password=pw, 
            role=d['role'], 
            profession=d.get('profession'), 
            city=d['city'], 
            phone=d['phone'], 
            lat=float(d.get('lat', 0)), 
            lng=float(d.get('lng', 0))
        )
        db.session.add(u)
        db.session.commit()
        return redirect('/')
    except:
        return "Email already exists!"

@app.route('/login', methods=['POST'])
def login():
    u = User.query.filter_by(email=request.form.get('email')).first()
    if u and bcrypt.check_password_hash(u.password, request.form.get('password')):
        session.update({"user_id": u.id, "user_name": u.username, "role": u.role, "user_city": u.city})
        if u.role == 'admin': return redirect(url_for('admin_dashboard'))
        if u.role == 'pro': return redirect(url_for('pro_dashboard'))
        return redirect(url_for('cust_dashboard'))
    return "Login Fail"

@app.route('/cust-dashboard')
def cust_dashboard():
    if 'user_id' not in session: return redirect('/')
    u = db.session.get(User, session['user_id'])
    o = Order.query.filter_by(customer_id=u.id).order_by(Order.id.desc()).all()
    return render_template('cust_dash.html', user=u, orders=o, professions=PROFESSIONS)

@app.route('/place-order', methods=['POST'])
def place_order():
    o = Order(
        customer_id=session['user_id'], 
        customer_name=session['user_name'], 
        service_needed=request.form['service'], 
        pickup_address=request.form.get('pickup_address'), 
        drop_address=request.form.get('drop_address'),
        payment_mode=request.form['payment_mode'], 
        cust_lat=float(request.form.get('lat', 0)), 
        cust_lng=float(request.form.get('lng', 0))
    )
    db.session.add(o)
    db.session.commit()
    pros = User.query.filter_by(role='pro', profession=o.service_needed, city=session.get('user_city')).all()
    return render_template('confirmation.html', order=o, professionals=pros)

@app.route('/pro-dashboard')
def pro_dashboard():
    if 'user_id' not in session: return redirect('/')
    u = db.session.get(User, session['user_id'])
    pending_orders = Order.query.filter_by(service_needed=u.profession, status='Pending').all()
    my_tasks = Order.query.filter_by(pro_id=u.id).all()
    return render_template('pro_dash.html', user=u, orders=pending_orders, tasks=my_tasks)

@app.route('/accept-order/<int:id>')
def accept_order(id):
    o = db.session.get(Order, id)
    if o:
        o.status, o.pro_id = 'Accepted', session['user_id']
        db.session.commit()
    return redirect(url_for('pro_dashboard'))

@app.route('/complete-job/<int:id>', methods=['POST'])
def complete_job(id):
    o = db.session.get(Order, id)
    amt = int(request.form.get('amount', 0))
    o.status, o.amount = 'Completed', amt
    if o.payment_mode == 'Wallet':
        c = db.session.get(User, o.customer_id)
        p = db.session.get(User, o.pro_id)
        if c.wallet >= amt:
            c.wallet -= amt
            p.wallet += amt
    db.session.commit()
    return redirect(url_for('pro_dashboard'))

@app.route('/admin-dashboard')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect('/')
    users = User.query.all()
    revenue = db.session.query(db.func.sum(Order.amount)).scalar() or 0
    return render_template('admin.html', users=users, revenue=revenue)
@app.route('/admin/delete-user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin': return redirect('/') 
    # User ko database mein dhoondein
    user_to_delete = db.session.get(User, user_id) 
    
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit() # Ye database se permanent delete kar dega
        print(f"User {user_id} terminated successfully.")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/chat/<int:order_id>')
def chat(order_id):
    o = db.session.get(Order, order_id)
    history = Message.query.filter_by(order_id=order_id).all()
    return render_template('chat.html', order=o, history=history)

@app.route('/upload-media', methods=['POST'])
def upload_media():
    file = request.files['file']
    order_id = request.form['order_id']
    msg_type = request.form['type']
    if file:
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        
        new_msg = Message(
            order_id=order_id,
            sender_id=session['user_id'],
            sender_name=session['user_name'],
            msg_type=msg_type,
            file_path='/static/uploads/' + filename
        )
        db.session.add(new_msg)
        db.session.commit()
        socketio.emit('new_msg', room=str(order_id))
    return jsonify({"status": "ok"})

@app.route('/rate-order/<int:id>', methods=['POST'])
def rate_order(id):
    o = db.session.get(Order, id)
    if o:
        o.rating = int(request.form.get('rating', 0))
        o.feedback = request.form.get('feedback', '')
        db.session.commit()
    return redirect(url_for('cust_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- SOCKET EVENTS ---
@socketio.on('join')
def on_join(data):
    join_room(str(data['order_id']))

@socketio.on('send_msg')
def handle_msg(data):
    msg = Message(
        order_id=data['order_id'],
        sender_id=session['user_id'],
        sender_name=session['user_name'],
        content=data['msg'],
        msg_type='text'
    )
    db.session.add(msg)
    db.session.commit()
    socketio.emit('new_msg', room=str(data['order_id']))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
