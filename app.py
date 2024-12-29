from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Database configuration
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/itsm_db'  # Replace username, password, and itsm_db with your MySQL credentials and database name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='End User')  # Roles: End User, Agent, Admin


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_description = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    channel = db.Column(db.String(100), nullable=True)
    requestor = db.Column(db.String(100), nullable=True)
    assignee = db.Column(db.String(100), nullable=True)
    impact = db.Column(db.String(50), nullable=True)
    urgency = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Open')


# Create tables within application context
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password='password123', role='Admin')
        db.session.add(admin_user)
        db.session.commit()


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('manage_tickets'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with app.app_context():
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['username'] = username
                session['role'] = user.role
                return redirect(url_for('manage_tickets'))
        return "Invalid username or password!", 401
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if role not in ['End User', 'Agent']:
            return "Invalid role selected!", 400
        if User.query.filter_by(username=username).first():
            return "Username already exists!", 400

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/tickets', methods=['GET'])
def manage_tickets():
    if 'username' not in session:
        return redirect(url_for('login'))

    tickets = Ticket.query.all()
    return render_template('manage_tickets.html', tickets=tickets)


@app.route('/tickets/create', methods=['GET', 'POST'])
def create_ticket():
    if 'username' not in session:
        return redirect(url_for('login'))

    categories = ['Hardware issue', 'Software issue', 'Network issue', 'Access issue']
    channels = ['Email', 'Phone', 'Self-service', 'Walk-up']
    impacts = ['High', 'Medium', 'Low']
    urgencies = ['High', 'Medium', 'Low']
    statuses = ['Open', 'Assigned', 'In Progress', 'Resolved', 'Closed']
    requestors = User.query.filter_by(role='End User').all()
    assignees = User.query.filter_by(role='Agent').all()

    if request.method == 'POST':
        new_ticket = Ticket(
            category=request.form.get('category'),
            short_description=request.form.get('short_description'),
            description=request.form.get('description'),
            channel=request.form.get('channel'),
            requestor=request.form.get('requestor'),
            assignee=request.form.get('assignee'),
            impact=request.form.get('impact'),
            urgency=request.form.get('urgency'),
            status=request.form.get('status')
        )
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for('manage_tickets'))

    return render_template('create_ticket.html', categories=categories, channels=channels, impacts=impacts,
                           urgencies=urgencies, statuses=statuses, requestors=requestors, assignees=assignees)


@app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
def view_ticket(ticket_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    ticket = Ticket.query.get_or_404(ticket_id)

    categories = ['Hardware issue', 'Software issue', 'Network issue', 'Access issue']
    channels = ['Email', 'Phone', 'Self-service', 'Walk-up']
    impacts = ['High', 'Medium', 'Low']
    urgencies = ['High', 'Medium', 'Low']
    statuses = ['Open', 'Assigned', 'In Progress', 'Resolved', 'Closed']
    requestors = User.query.filter_by(role='End User').all()
    assignees = User.query.filter_by(role='Agent').all()

    if request.method == 'POST':
        ticket.category = request.form.get('category')
        ticket.short_description = request.form.get('short_description')
        ticket.description = request.form.get('description')
        ticket.channel = request.form.get('channel')
        ticket.requestor = request.form.get('requestor')
        ticket.assignee = request.form.get('assignee')
        ticket.impact = request.form.get('impact')
        ticket.urgency = request.form.get('urgency')
        ticket.status = request.form.get('status')
        db.session.commit()
        return redirect(url_for('manage_tickets'))

    return render_template('update_ticket.html', ticket=ticket, categories=categories, channels=channels,
                           impacts=impacts, urgencies=urgencies, statuses=statuses, requestors=requestors,
                           assignees=assignees)


if __name__ == '__main__':
    app.run(debug=True)
