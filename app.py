from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_mysqldb import MySQL
import os
from werkzeug.utils import secure_filename 

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/files/cv'
app.config['SECRET_KEY'] = '1234'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskapp'

mysql = MySQL(app)

@app.route('/')
def index():
   

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_type = request.form['user_type']
        if user_type == 'student':
            # Get student form data
            first_name = request.form['first_name']
            surname = request.form['surname']
            email = request.form['email']
            resume_path = request.files['resume'].filename
            cv = request.files['resume']
            filename = secure_filename(cv.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cv.save(file_path)
            password = request.form['password']

            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM students WHERE email = %s", (email,))
            user_data = cur.fetchone()

            if user_data:
                # Email already exists, redirect to a page showing error or handle accordingly
                flash('Email associated with an existing account', 'error')
                return redirect(url_for('signup'))

            # Insert student data into the database
            cur.execute("INSERT INTO students (first_name, surname, email, resume_path, password) VALUES (%s, %s, %s, %s, %s)",(first_name, surname, email, resume_path, password))
            mysql.connection.commit()
            cur.close()

        elif user_type == 'organization':
            # Get organization form data
            name = request.form['name']
            website_link = request.form['website_link']
            email = request.form['email']
            password = request.form['password']

            # Insert organization data into the database
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO organizations (name, website_link, email, password) VALUES (%s, %s, %s, %s)",(name, website_link, email, password))
            mysql.connection.commit()
            cur.close()

        flash('Sign up successful! Please log in to your account.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form['user_type']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        if user_type == 'student':
            cur.execute("SELECT * FROM students WHERE email = %s AND password = %s", (email, password))
        elif user_type == 'organization':
            cur.execute("SELECT * FROM organizations WHERE email = %s AND password = %s", (email, password))

        user = cur.fetchone()

        if user:
            session['logged_in'] = True
            session['user_type'] = user_type
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            # Redirect to a dashboard or profile page after successful login
            if user_type == 'student':
                return redirect(url_for('student_dashboard'))
            elif user_type == 'organization':
                return redirect(url_for('organization_dashboard'))
        else:
            flash('Login failed. Invalid credentials.', 'error')
        cur.close()

    return render_template('login.html')

@app.route('/organization', methods=['GET', 'POST'])
def organization_dashboard():
    id = session.get('user_id')
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT * FROM organizations where id = %s',(id,))
    organization = cursor.fetchone()

    cursor.execute("SELECT * FROM internships WHERE organization_id = %s", (id,))
    internships = cursor.fetchall()

    cursor.execute("SELECT * FROM jobs WHERE organization_id = %s", (id,))
    jobs = cursor.fetchall()

    # Store user information in the global context (g)
    g.user = organization
    g.internships = internships
    g.jobs = jobs
    return render_template('organization_dashboard.html',)

@app.route('/student', methods=['GET', 'POST'])
def student_dashboard():
    id = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM students where id = %s',(id,))
    organization = cursor.fetchone()
    cursor.execute("SELECT internships.*, organizations.name, organizations.website_link FROM internships JOIN organizations ON internships.organization_id = organizations.id LEFT JOIN internship_applications ON internships.id = internship_applications.intern_id AND internship_applications.student_id = %s WHERE internship_applications.intern_id IS NULL",(id,))
    internships = cursor.fetchall()
    cursor.execute("SELECT jobs.*, organizations.name, organizations.website_link FROM jobs JOIN organizations ON jobs.organization_id = organizations.id LEFT JOIN job_applications ON jobs.id =job_applications.job_id AND job_applications.student_id = %s WHERE job_applications.job_id IS NULL;",(id,))
    jobs = cursor.fetchall()
    g.user = organization
    g.internships = internships
    g.jobs = jobs
    return render_template('student_dashboard.html',)

@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()
    flash('Log out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/organization/new', methods=['GET','POST'])
def new_opportunity():
    if request.method == 'POST':
        type = request.form['type']
        if type == 'internship':
            id = request.form['id']
            duration = request.form['duration']
            description = request.form['description']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO internships(duration, description, organization_id) VALUES (%s, %s, %s)", (duration,description,id))
            mysql.connection.commit()
            cur.close()
            flash('Opportunity added successfully.', 'success')
            return redirect(url_for('organization_dashboard'))
        elif type == 'job':
            id = request.form['id']
            position = request.form['position']
            description = request.form['description']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO `jobs`(`position`, `description`, `organization_id`) VALUES (%s, %s, %s)", (position,description,id))
            mysql.connection.commit()
            cur.close()
            flash('Opportunity added successfully.', 'success')
            return redirect(url_for('organization_dashboard'))

@app.route('/organization/edit', methods=['POST','GET'])
def edit():
    id = request.args.get('id')
    type = request.args.get('type')
    if type == 'internship':
            duration = request.form['duration']
            description = request.form['description']
            cur = mysql.connection.cursor()
            cur.execute("UPDATE `internships` SET `duration`= %s,`description`= %s WHERE `id` = %s", (duration,description,id))
            mysql.connection.commit()
            cur.close()
            flash('Internship details updated successfully.', 'success')
            return redirect(url_for('organization_dashboard'))
    elif type == 'job':
            description = request.form['description']
            cur = mysql.connection.cursor()
            cur.execute("UPDATE `jobs` SET `description`= %s WHERE `id` = %s", (description,id))
            mysql.connection.commit()
            cur.close()
            flash('Job details updated successfully.', 'success')
            return redirect(url_for('organization_dashboard'))
    
@app.route('/organization/delete', methods=['POST','GET'])
def delete():
    id = request.args.get('id')
    type = request.args.get('type')
    if type == 'internship':
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM `internships` WHERE `id` = %s", (id))
            mysql.connection.commit()
            cur.close()
            flash('Internship opportunity deleted successfully.', 'success')
            return redirect(url_for('organization_dashboard'))
    elif type == 'job':
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM `jobs` WHERE `id` = %s", (id))
            mysql.connection.commit()
            cur.close()
            flash('Job opportunity deleted successfully.', 'success')
            return redirect(url_for('organization_dashboard'))

@app.route('/student/apply', methods=['POST','GET'])
def apply():
    student_id = request.args.get('student_id')
    type = request.args.get('type')
    if type == 'internship':
            intern_id = request.args.get('intern_id')
            org_id = request.args.get('org_id')
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO `internship_applications`(`intern_id`, `organization_id`, `student_id`) VALUES (%s,%s,%s)",(intern_id,org_id,student_id))
            mysql.connection.commit()
            cur.close()
            flash('Application submitted successfully.', 'success')
            return redirect(url_for('student_dashboard'))
    elif type == 'job':
            job_id = request.args.get('job_id')
            org_id = request.args.get('org_id')
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO `job_applications` (`job_id`, `organization_id`, `student_id`) VALUES (%s,%s,%s)",(job_id,org_id,student_id))
            mysql.connection.commit()
            cur.close()
            flash('Application submitted successfully.', 'success')
            return redirect(url_for('student_dashboard'))

@app.route('/student/applications', methods=['POST','GET'])
def applications():
    id = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM students where id = %s',(id,))
    student = cursor.fetchone()
    cursor.execute("SELECT internship_applications.*, internships.*, organizations.name, organizations.website_link FROM internship_applications JOIN organizations ON internship_applications.organization_id = organizations.id LEFT JOIN internships ON internship_applications.intern_id = internships.id AND internship_applications.student_id = %s WHERE internship_applications.intern_id IS NOT NULL ORDER BY internship_applications.date DESC;",(id,))
    internships = cursor.fetchall()
    cursor.execute("SELECT job_applications.*, jobs.*, organizations.name, organizations.website_link FROM job_applications JOIN organizations ON job_applications.organization_id = organizations.id LEFT JOIN jobs ON job_applications.job_id = jobs.id AND job_applications.student_id = %s WHERE job_applications.job_id IS NOT NULL ORDER BY job_applications.date DESC;",(id,))
    jobs = cursor.fetchall()
    g.user = student
    g.internships = internships
    g.jobs = jobs
    return render_template('applications.html',)

@app.route('/organisation/responses', methods=['POST','GET'])
def responses():
    id = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM organizations where id = %s',(id,))
    organization = cursor.fetchone()
    cursor.execute("SELECT internship_applications.*, internships.*, students.first_name, students.surname, students.resume_path FROM internship_applications JOIN students ON internship_applications.student_id = students.id LEFT JOIN internships ON internship_applications.intern_id = internships.id WHERE internship_applications.organization_id = %s AND internship_applications.status = 'pending' GROUP BY internships.description ORDER BY internship_applications.date DESC;",(id,))
    internships = cursor.fetchall()
    cursor.execute("SELECT job_applications.*, jobs.*, students.first_name, students.surname, students.resume_path FROM job_applications JOIN students ON job_applications.student_id = students.id LEFT JOIN jobs ON job_applications.job_id = jobs.id WHERE job_applications.organization_id = %s AND job_applications.status = 'pending' GROUP BY jobs.position ORDER BY job_applications.date DESC;",(id,))
    jobs = cursor.fetchall()
    g.user = organization
    g.internships = internships
    g.jobs = jobs
    return render_template('responses.html',)

@app.route('/organisation/responses/accept', methods=['POST','GET'])
def accept():
    id = request.args.get('id')
    type = request.args.get('type')
    if type == 'intern':
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE `internship_applications` SET `status`= 'Accepted' WHERE `id` = %s",(id,))
        mysql.connection.commit()
    if type == 'job':
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE `job_applications` SET `status`= 'Accepted' WHERE `id` = %s",(id,))
        mysql.connection.commit()
    flash('Application accepted.', 'success')
    return redirect(url_for('responses'))


@app.route('/organisation/responses/turndown', methods=['POST','GET'])
def turndown():
    id = request.args.get('id')
    type = request.args.get('type')
    if type == 'intern':
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE `internship_applications` SET `status`= 'Turned down' WHERE `id` = %s",(id,))
        mysql.connection.commit()
    if type == 'job':
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE `job_applications` SET `status`= 'Turned down' WHERE `id` = %s",(id,))
        mysql.connection.commit()
    flash('Application turned down.', 'success')
    return redirect(url_for('responses'))

if __name__ == '__main__':
    app.run(debug=True)
