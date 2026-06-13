from flask import Flask, request, render_template, redirect, session, url_for, flash
from werkzeug.utils import secure_filename
import os
from models import db, User, Course


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'

# ✅ File upload config
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ✅ Initialize SQLAlchemy with app
db.init_app(app)

# ✅ This must be done inside the app context
with app.app_context():
    db.create_all()  # This will create tables if not exist

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    if session.get('email'):
        user = User.query.filter_by(email=session['email']).first()
        if not user.image:
            user.image = 'default.png'
        return render_template('dashboard.html', user=user)
    
    flash("You must be logged in to access the dashboard.", "warning")
    return redirect('/login')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'email' not in session:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        user.branch = request.form['branch']
        user.year = request.form['year']

        # Handle image upload
        file = request.files.get('profile_pic')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            user.image = filename

        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for('profile'))

    user.image = user.image if user.image else None
    return render_template('profile.html', user=user)


@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    if 'email' not in session:
        flash("Please log in to delete your photo.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()
    if user and user.image != 'default.png':
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], user.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            flash("Error deleting image: " + str(e), "danger")
            return redirect(url_for('profile'))

        user.image = 'default.png'
        db.session.commit()
        flash("Profile photo deleted.", "info")
    else:
        flash("No photo to delete.", "warning")

    return redirect(url_for('profile'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        branch = request.form.get('branch')
        year = request.form.get('year')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Try logging in.", "danger")
            return redirect('/register')

        new_user = User(name=name, email=email, password=password, branch=branch, year=year)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            session['user_id'] = user.id  # ✅ ADD THIS LINE
            flash("Login successful!", "success")
            return redirect('/dashboard')
        else:
            flash("Invalid email or password.", "danger")
            return redirect('/login')

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect('/login')

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        description = request.form['description']

        existing = Course.query.filter_by(code=code).first()
        if existing:
            flash("Course code already exists.", "danger")
            return redirect('/add_course')

        course = Course(code=code, name=name, description=description)
        db.session.add(course)
        db.session.commit()
        flash("Course added!", "success")
        return redirect('/add_course')

    return render_template('add_course.html')

@app.route('/courses')
def all_courses():
    if 'user_id' not in session:
        flash("Please log in to view courses.", "warning")
        return redirect('/login')

    user = User.query.get(session['user_id'])
    courses = Course.query.all()

    # ✅ Corrected enrolled course IDs
    enrolled_ids = [course.id for course in user.courses]

    return render_template('courses.html', user=user, courses=courses, enrolled_ids=enrolled_ids)

@app.route('/my_courses')
def my_courses():
    if 'user_id' not in session:
        flash("Please log in to view your enrolled courses.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('my_courses.html', user=user)




@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    if 'email' not in session:
        flash("Please log in to enroll.", "danger")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()

    course = Course.query.get_or_404(course_id)

    if course in user.courses:
        flash(f"Already enrolled in {course.name}.", "info")
    else:
        user.courses.append(course)
        db.session.commit()
        flash(f"Enrolled in {course.name}!", "success")

    return redirect(url_for('all_courses'))



if __name__ == '__main__':
    app.run(debug=True)


