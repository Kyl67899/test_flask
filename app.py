"""
Kyle Parsotan
Sept. 28 2025
Portfolio using Flask and postgresql
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
import os

from dotenv import load_dotenv
# Load variables from .env file
load_dotenv(dotenv_path=".env.local")

app = Flask(__name__, template_folder="temp")
# set the routing to the main page
# 'route' decorator is used to access the root URL

app.secret_key = os.urandom(24).hex()
app.config["SECRET_KEY"] = app.secret_key

#config for the postgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('POSTGRESQL_DB')
app.config["SESSION_PERMANENT"] = False  # ✅ Prevent session persistence beyond logout
app.config["SESSION_TYPE"] = "filesystem"  # ✅ Store sessions securely

admin_username = os.getenv("ADMIN_USERNAME", "admin")
admin_password = os.getenv("ADMIN_PASSWORD", "yourpassword")

SQLALCHEMY_TRACK_MODIFICATIONS = False

# #call in the db for postgreSQL
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# db.init_app(app)

from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('APP_EMAIL')  # your Gmail address
app.config['MAIL_PASSWORD'] = os.getenv('APP_EMAIL_PASSWORD')      # use Gmail app password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('APP_EMAIL')

print(os.getenv("APP_EMAIL"))
print(os.getenv("APP_EMAIL_PASSWORD"))

mail = Mail(app)

############ Class Model ##############

# # import db from app
# from app import db

# create a class for project
class Project(db.Model):
    __tablename__ = 'project'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tools = db.Column(db.ARRAY(db.String))  # or a relationship table
    skills = db.Column(db.ARRAY(db.String))
    objective = db.Column(db.Text)
    summary = db.Column(db.Text)
    image_url = db.Column(db.String)
    date_created= db.Column(db.DateTime, default=datetime.utcnow)
    
# admin class 
class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password, bcrypt):
        return bcrypt.check_password_hash(self.password_hash, password)

class ContactInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    subject = db.Column(db.String(150))
    message = db.Column(db.Text)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)

############ Class Model ##############

############ Route ##############

# Home 
@app.route('/')
def index():
    # recent project
    recent_projects = Project.query.order_by(Project.date_created.desc()).limit(5).all()
    print(recent_projects)
    return render_template("index.html", recent_projects=recent_projects)

# project
@app.route("/project")
def project():
    category = request.args.get("category")
    categories = db.session.query(Project.category).distinct().all()
    categories = [c[0] for c in categories]

    if category:
        filter_projects = Project.query.filter_by(category=category).all()
    else:
        filter_projects = Project.query.all()

    return render_template("project.html",
                           projects=filter_projects,
                           categories=categories,
                           selected_category=category)
    
# Project id
@app.route('/project/<int:id>', endpoint='project_detail')
def project_detail(id):
    project = Project.query.get_or_404(id)
    return render_template('project_detail.html', project=project)
    
# add project
from flask import flash, request, redirect, url_for, render_template
import logging

@app.route('/add_project', methods=['GET', 'POST'], endpoint='add_project')
@app.route('/add_project/<int:id>', methods=['GET', 'POST'])
def add_project(id=None):
    project = Project.query.get(id) if id else None

    if request.method == 'POST':
        try:
            # Validate required fields
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            objective = request.form.get('objective', '').strip()
            summary = request.form.get('summary', '').strip()
            image_url = request.form.get('image_url', '').strip()
            category = request.form.get('category_custom', '').strip() or request.form.get('category', '').strip()

            if not title or not description or not category:
                return render_template('add_project.html', project=project)

            tools_list = [tool.strip() for tool in request.form.get('tools', '').split(',') if tool.strip()]
            skills_list = [skill.strip() for skill in request.form.get('skills', '').split(',') if skill.strip()]

            if project:
                # Update existing project
                project.title = title
                project.description = description
                project.category = category
                project.tools = tools_list
                project.skills = skills_list
                project.objective = objective
                project.summary = summary
                project.image_url = image_url
                flash('Project updated successfully!', 'success')
            else:
                # Create new project
                project = Project(
                    title=title,
                    description=description,
                    category=category,
                    tools=tools_list,
                    skills=skills_list,
                    objective=objective,
                    summary=summary,
                    image_url=image_url,
                    date_created=datetime.utcnow()
                )
                db.session.add(project)
                flash('New Project created successfully!', 'success')

            db.session.commit()
            return redirect(url_for('project'))

        except Exception as e:
            db.session.rollback()
            logging.exception("Error adding/updating project")
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('add_project.html', project=project)

    return render_template('add_project.html', project=project)

# add a hidden admin dashboard to manage the skills, projects, contact, resume info
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # simple access control 
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
    
    projects = Project.query.order_by(Project.date_created.desc()).limit(5).all()
    # print(recent_projects)
    return render_template("admin.html", projects=projects)

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            admin = AdminUser.query.filter_by(username=username).first()
            if admin and admin.check_password(password, bcrypt):
                session['admin_logged_in'] = True
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials')
        except Exception as e: 
            db.session.rollback()
            logging.exception("Error logging in")
            flash(f'An error occurred: {str(e)}', 'danger')
    return render_template('login.html')

# logout
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    projects = Project.query.all()
    return render_template('dashboard.html', projects=projects)

# delete projects
@app.route('/delete_project/<int:id>', methods=['POST'])
def delete_project(id):
    try:
        project = Project.query.get_or_404(id)
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'danger')

    return redirect(url_for('project'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# contact

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            email = request.form.get("email")
            subject = request.form.get("subject")
            message_body = request.form.get("message")
            # Save to database
            contact_entry = ContactInfo(
                name=name,
                email=email,
                subject=subject,
                message=message_body
                )
            
            db.session.add(contact_entry)
            db.session.commit()
            
            # Send email
            try:
                msg = Message(
                    subject=f"New Contact: {subject}",
                    sender=app.config["MAIL_DEFAULT_SENDER"],
                    recipients=[app.config["MAIL_USERNAME"]],
                    body=f"From: {name} <{email}>\n\n{message_body}"
                ).send(msg)
                flash("Message sent and saved successfully!", "success")
            except Exception as e:
                flash(f"Email failed to send: {str(e)}", "danger")
        except Exception as e:
            print('Error:', e)
            flash('Something went wrong. Please try again', "danger")
        return redirect(url_for("contact"))

    return render_template("contact.html")

with app.app_context():
    db.create_all()
    if not AdminUser.query.filter_by(username=admin_username).first():
        hashed_pw = bcrypt.generate_password_hash("yourpassword").decode('utf-8')
        admin = AdminUser(username="admin", password_hash=hashed_pw)
        db.session.add(admin)
        db.session.commit()
        print(AdminUser.query.all())
        
# set the 'app' to run if you execute the file directly(not when it is imported)
if __name__ == '__main__':
    app.run(debug=True)