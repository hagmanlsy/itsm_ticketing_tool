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
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='End User')  # Roles: End User, Agent, Admin
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Approved, Rejected


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_description = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    channel = db.Column(db.String(100), nullable=True)
    requestor = db.Column(db.String(100), nullable=True)
    assignment_group = db.Column(db.String(100), nullable=True)
    assignee = db.Column(db.String(100), nullable=True)
    impact = db.Column(db.String(50), nullable=True)
    urgency = db.Column(db.String(50), nullable=True)
    priority = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Open')
    resolution_code = db.Column(db.String(50), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    users = db.relationship('User', secondary='group_users', backref='groups')

class GroupUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# Create tables within application context
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            first_name='Admin',
            last_name='User',
            email='admin@example.com',
            username='admin',
            password='password123',
            role='Admin',
            status='Approved'
        )
        db.session.add(admin_user)
        db.session.commit()


@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    role = session.get('role')
    firstname = session.get('first_name')
    lastname = session.get('last_name')
    return render_template('home.html', username=username, role=role, firstname=firstname, lastname=lastname)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with app.app_context():
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                if user.status == 'Pending':
                    return "Your account is pending approval by an administrator.", 403
                if user.status == 'Rejected':
                    return "Your account has been rejected by an administrator.", 403
                if user.status == 'Approved':
                    session['username'] = username
                    session['role'] = user.role
                    session['first_name'] = user.first_name
                    session['last_name'] = user.last_name
                    return redirect(url_for('home'))
        return "Invalid username or password!", 401
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if role not in ['End User', 'Agent']:
            return "Invalid role selected!", 400
        if User.query.filter_by(username=username).first():
            return "Username already exists!", 400
        if User.query.filter_by(email=email).first():
            return "Email already exists!", 400

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password,
            role=role,
            status='Pending'
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/admin/pending_users', methods=['GET', 'POST'])
def pending_users():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    pending_users = User.query.filter_by(status='Pending').all()
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        user = User.query.get(user_id)
        if user:
            if action == 'approve':
                user.status = 'Approved'
            elif action == 'reject':
                user.status = 'Rejected'
            db.session.commit()
        return redirect(url_for('pending_users'))

    return render_template('pending_users.html', users=pending_users)


@app.route('/admin/user_management', methods=['GET', 'POST'])
def user_management():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        if action == 'delete':
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
        elif action == 'update':
            user = User.query.get(user_id)
            if user:
                user.role = request.form.get('role')
                db.session.commit()
        else:
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password,
                role=role,
                status='Approved'
            )
            db.session.add(new_user)
            db.session.commit()

    users = User.query.all()
    return render_template('user_management.html', users=users)

@app.route('/admin/group_management', methods=['GET', 'POST'])
def group_management():
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            group_id = request.form.get('group_id')
            group = Group.query.get(group_id)
            if group:
                db.session.delete(group)
                db.session.commit()
        elif action == 'create':
            group_name = request.form.get('group_name')
            if not Group.query.filter_by(name=group_name).first():
                new_group = Group(name=group_name)
                db.session.add(new_group)
                db.session.commit()

    groups = Group.query.all()
    return render_template('group_management.html', groups=groups)


@app.route('/admin/group_management/<int:group_id>', methods=['GET'])
def view_group_users(group_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    group = Group.query.get_or_404(group_id)
    users = group.users
    return render_template('group_users.html', group=group, users=users)

@app.route('/admin/group_management/<int:group_id>/add_user', methods=['GET', 'POST'])
def add_user_to_group(group_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    group = Group.query.get_or_404(group_id)
    users = User.query.filter(User.role == 'Agent', ~User.groups.any(id=group_id)).all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user and user.role == 'Agent' and user not in group.users:
            group.users.append(user)
            db.session.commit()
            return redirect(url_for('add_user_to_group', group_id=group_id))

    return render_template('add_user_to_group.html', group=group, users=users)


@app.route('/admin/group_management/<int:group_id>/remove_user', methods=['POST'])
def remove_user_from_group(group_id):
    if 'username' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    user_id = request.form.get('user_id')
    group = Group.query.get_or_404(group_id)
    user = User.query.get(user_id)
    if user and user in group.users:
        group.users.remove(user)
        db.session.commit()

    return redirect(url_for('view_group_users', group_id=group_id))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('first_name', None)
    session.pop('last_name', None)
    return redirect(url_for('login'))


@app.route('/tickets', methods=['GET'])
def manage_tickets():
    if 'username' not in session:
        return redirect(url_for('login'))

    filter_assigned = request.args.get('assigned_to_me', 'false')
    if session['role'] == 'End User':
        tickets = Ticket.query.filter_by(requestor=session['username']).all()
    else:
        if filter_assigned == 'true':
            tickets = Ticket.query.filter_by(assignee=session['username']).all()
        else:
            tickets = Ticket.query.all()

    return render_template('manage_tickets.html', tickets=tickets, show_back_to_dashboard=True,
                           filter_assigned=filter_assigned)


@app.route('/tickets/<int:ticket_id>', methods=['GET', 'POST'])
def update_ticket(ticket_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    ticket = Ticket.query.get_or_404(ticket_id)

    categories = ['Hardware issue', 'Software issue', 'Network issue', 'Access issue']
    channels = ['Email', 'Phone', 'Self-service', 'Walk-up']
    impacts = ['High', 'Medium', 'Low']
    urgencies = ['High', 'Medium', 'Low']
    statuses = ['Open', 'In Progress', 'Resolved', 'Closed']
    requestors = User.query.filter_by(role='End User').all()
    groups = Group.query.all()

    # Fetch assignees based on assignment group
    assignment_group = ticket.assignment_group
    if assignment_group:
        assignees = User.query.join(GroupUsers).join(Group).filter(
            Group.name == assignment_group,
            User.role == 'Agent'
        ).all()
    else:
        assignees = User.query.filter_by(role='Agent').all()

    if request.method == 'POST':
        ticket.short_description = request.form.get('short_description')
        ticket.description = request.form.get('description')
        ticket.category = request.form.get('category')
        ticket.channel = request.form.get('channel')
        ticket.requestor = request.form.get('requestor')
        ticket.assignment_group = request.form.get('assignment_group')

        # Update assignee based on selected assignment group
        assignment_group = request.form.get('assignment_group')
        if assignment_group:
            assignees = User.query.join(GroupUsers).join(Group).filter(
                Group.name == assignment_group,
                User.role == 'Agent'
            ).all()

        ticket.assignee = request.form.get('assignee')
        ticket.impact = request.form.get('impact')
        ticket.urgency = request.form.get('urgency')
        ticket.priority = request.form.get('priority')
        ticket.status = request.form.get('status')

        # Handle resolution fields for Resolved/Closed statuses
        if ticket.status in ['Resolved', 'Closed']:
            ticket.resolution_code = request.form.get('resolution_code')
            ticket.resolution_notes = request.form.get('resolution_notes')
        else:
            ticket.resolution_code = None
            ticket.resolution_notes = None

        db.session.commit()
        return redirect(url_for('manage_tickets'))

    return render_template(
        'update_ticket.html',
        ticket=ticket,
        categories=categories,
        channels=channels,
        impacts=impacts,
        urgencies=urgencies,
        statuses=statuses,
        requestors=requestors,
        groups=groups,
        assignees=assignees
    )



@app.route('/tickets/create', methods=['GET', 'POST'])
def create_ticket():
    if 'username' not in session:
        return redirect(url_for('login'))

    categories = ['Hardware issue', 'Software issue', 'Network issue', 'Access issue']
    channels = ['Email', 'Phone', 'Self-service', 'Walk-up']
    impacts = ['High', 'Medium', 'Low']
    urgencies = ['High', 'Medium', 'Low']
    statuses = ['Open', 'In Progress', 'Resolved', 'Closed']
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


if __name__ == '__main__':
    app.run(debug=True)
