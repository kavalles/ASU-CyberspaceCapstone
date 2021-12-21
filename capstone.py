from flask import Flask, render_template, url_for, flash, redirect, url_for, session, logging, request, make_response, Response
from flask_mysqldb import MySQL
from forms import RegistrationForm, LoginForm, SubmitForm, FileUploadForm, ChangePasswordForm, BulkRegisterForm, ArtifactForm, EditArtifactForm, PhaseManagementForm
from passlib.hash import sha256_crypt
from functools import wraps
import datetime
from flask_wtf.file import FileField, FileRequired
import csv
from werkzeug.utils import secure_filename
import os
from os.path import join, dirname, realpath
import pandas as pd
#from flask_user import login_required, roles_required, UserManager, UserMixin, SQLAlchemyAdapter
#from flask_login import LoginManager
import pymysql
#import StringIO
import io
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Init app
app = Flask(__name__, template_folder='Templates')
app.config['SECRET_KEY'] = '1d88045479be17986418611768db9c4b'

# Config database
app.config['MYSQL_HOST'] = 'cyberdb.crgmvqs7d5by.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'capstone'
app.config['MYSQL_PASSWORD'] = 'cyberspace'
app.config['MYSQL_DB'] = 'innodb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Config database on VM
#app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = 'Password123!'
#app.config['MYSQL_DB'] = 'scoringEngine'


# init database
db = MySQL(app)

UPLOAD_FOLDER = 'static/files'
ALLOWED_EXTENSIONS = {'file', 'csv', 'csvfile'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



#Role values
TEAM = 0
ASSESSOR = 1
ADMIN = 2


#_________Access Control__________

# Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#check user role (team)
def is_team(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['role'] is TEAM:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized', 'danger')
            return redirect(url_for('index'))
    return wrap


# Check user role (assessor) aka not a team
def is_assessor(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['role'] is TEAM:
            flash('Unauthorized', 'danger')
            return redirect(url_for('index'))
        else:
            return f(*args, **kwargs)
            
    return wrap

# Check user role (admin)
def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['role'] is ADMIN:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized', 'danger')
            return redirect(url_for('index'))
    return wrap


#________routes______________

# Bassic home, no login required
@app.route("/")
def index():
    return render_template("home.html")


# Assessors Home Page, login Required, assessor or admin role required
@app.route("/assessorhome")
@is_logged_in         
@is_assessor
def assessorhome():
    return render_template('assessorHome.html', title='Assessor Home')


# Player home, login Required
@app.route("/playerhome", methods=['GET', 'POST'])
@is_logged_in
@is_team
def playerhome():
    form = SubmitForm()
    userID = session['userId'] #updated to get the userId of the correct team submitting
    
    # Create cursor
    cur = db.connection.cursor()

    #update submission history table
    total = cur.execute("SELECT * FROM UserArtifactSubmission WHERE userId = %s", [userID])
    results = cur.fetchall()

    # Close connection
    cur.close() 

    if form.validate_on_submit():
        artifact = form.artifact.data
        timestamp = datetime.datetime.now()
       # artifactSubmissionID = 1
        
        # Create cursor
        cur = db.connection.cursor()
        duplicate = cur.execute("SELECT * FROM UserArtifactSubmission WHERE userId = %s AND submissionString = %s", [userID, artifact])
        if duplicate > 0:
            error = "You already submitted this artifact."
            form.artifact.data =''
            return render_template('playerHome.html', form=form, title='Team Home', submissions=results, total=total, error=error)

        #add new artifact 
        cur.execute("INSERT INTO UserArtifactSubmission(userId, submissionString, updatedTimeStamp) VALUES(%s, %s, %s)", (int(userID), artifact, timestamp))

        # Commit to DB
        db.connection.commit()
        flash('Artifact Successfully Submitted!', 'success')

        #update submission history table
        total = cur.execute("SELECT * FROM UserArtifactSubmission WHERE userId = %s", [userID])
        results = cur.fetchall()

        # Close connection
        cur.close()
        form.artifact.data =''

    return render_template('playerHome.html', form=form, title='Team Home', submissions=results, total=total)

# Admin page, login Required
@app.route("/admin")
@is_logged_in
@is_admin
def admin():
    return render_template('admin.html', title='Admin')


# Select team to view, login assessor Required
@app.route("/teams", methods=['GET', 'POST'])
@is_logged_in
@is_assessor
def teams():
    # create cursor
    cursor = db.connection.cursor()

    # get all teamIds from db
    cursor.execute('SELECT userId, username FROM User WHERE roleId = 0')   

    # fetch list of all team data to pass to html
    teamList = cursor.fetchall()
    #teamSelected = request.form.get("dropdown")
    
    # close connection
    cursor.close() 
        
    return render_template('teams.html', title='Teams', teamList=teamList)

# plots all teams' correct/incorrect submission counts for overview
@app.route('/plot_teams')
def plot_teams():
    cursor = db.connection.cursor()
    
    # create empty lists
    successes = []
    failures = []
    labels = []

    # create list of only player users
    cursor.execute('SELECT userId, userName FROM User WHERE roleId = 0')
    playerList = cursor.fetchall()
        
    # iterate through list to get success/fail counts by players
    for user in playerList:
        uID = str(user.get('userId'))
        
        # create list of team names for graph
        labels.append(user.get('userName'))

        # get count of successful submissions for each team
        queryS = ('''SELECT uas.submissionString 
                        FROM UserArtifactSubmission uas
                        INNER JOIN Artifact a
                            ON uas.submissionString = a.artifactString
                        WHERE uas.userId = %s
                        ''')
        s = cursor.execute(queryS, [uID])
        successes.append(s)

        # get count of failed submissions for each team
        queryF = ('''SELECT
                        uas.submissionString
                        FROM User
                        INNER JOIN UserArtifactSubmission uas
                            ON User.userId = uas.userId
                        LEFT JOIN Artifact a
                        ON uas.submissionString = a.artifactString
                        WHERE a.artifactString IS NULL
                            AND uas.userId = %s'''
        )
        f = cursor.execute(queryF, [uID])
        failures.append(f)
    cursor.close()

    fig = Figure()
    x = np.arange(len(labels))
    width = 0.35

    # force label to use ints
    maxS = max(successes)
    maxF = max(failures)
    topEnd = max(maxS,maxF)
    intsRange = range(0, topEnd+1)

    # create double bars
    fig, ax = plt.subplots()
    rects2 = ax.barh(x - width/2, successes, width, label='Correct')
    rects1 = ax.barh(x + width/2, failures, width, label='Incorrect')

    # flip order of teams and rects for top down rather than bottom up
    ax.invert_yaxis()

    ax.set_xticks(intsRange)
    ax.set_xlabel('Submissions')
    ax.set_ylabel('Teams')
    ax.set_title('Submissions by Team')
    ax.set_yticks(x)
    ax.set_yticklabels(labels)
    ax.legend(bbox_to_anchor=(1.1, 1.05))

    ax.bar_label(rects2, padding=3)
    ax.bar_label(rects1, padding=3)

    fig.tight_layout()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()

    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'img/png'
    return response

# Team Submissions, login assessor required
@app.route("/teamProgress", methods=['GET', 'POST'])
@is_logged_in
@is_assessor
def teamProgress():
    if request.method == 'POST':

        # create cursor
        cursor = db.connection.cursor()


        # fetch list of all team data to pass to html
        cursor.execute('SELECT userId, username FROM User WHERE roleId = 0')
        teamList = cursor.fetchall()

        # get post from dropdown on team
        team_id = request.form.get('dropdown')

        # get username of team from dropdown
        name_query = ('''SELECT username
                        FROM User WHERE User.userId = %s''')

        data = (team_id,)
        cursor.execute(name_query, data)
        team_name = cursor.fetchone()

        # build query for successful submissions
        success_query = ('''SELECT 
        	            User.username, 
	                        uas.userArtifactSubmissionId, 
	                        uas.submissionString,
	                        uas.updatedTimeStamp,
                            a.phaseId 
                        FROM User
                        INNER JOIN UserArtifactSubmission uas
	                        ON User.userId = uas.userId
                        INNER JOIN Artifact a
	                        ON uas.submissionString = a.artifactString
                        WHERE User.userId = %s
                        ORDER BY a.phaseId'''
        )
        

        # uses dropdown selection from teams to filter submissions by teams
        totalCorrect = cursor.execute(success_query, data)
        results = cursor.fetchall()
        


        # query failed submissions
        failed_query = ('''SELECT
                        User.username,
                        uas.userArtifactSubmissionId,
                        uas.submissionString,
                        uas.updatedTimeStamp 
                        FROM User
                        INNER JOIN UserArtifactSubmission uas
                            ON User.userId = uas.userId
                        LEFT JOIN Artifact a
                        ON uas.submissionString = a.artifactString
                        WHERE a.artifactString IS NULL
                            AND uas.userId = %s
                        ORDER BY uas.updatedTimeStamp'''
        )

        totalIncorrect = cursor.execute(failed_query, data)
        results2 = cursor.fetchall()


        #get total number of correct artifacts in the exercise
        total = totalCorrect + totalIncorrect

        cursor.close()        
        
        return render_template('teamProgress.html', title='Team Progress', team_name=team_name, results=results, results2=results2, teamList=teamList, totalCorrect = totalCorrect, totalIncorrect = totalIncorrect, total=total)

# Phases page, login assessor Required
@app.route("/phases", methods=['GET', 'POST'])
@is_logged_in
@is_assessor
def phases():
    cursor = db.connection.cursor()

    # fetch list of all team data to pass to html
    cursor.execute('SELECT phaseId, name FROM Phase')
    phaseList = cursor.fetchall()

    # get post from dropdown menu
    phase_id = request.form.get('dropdown')

    # get correct submissions for selected phase
    phase_query = ('''SELECT a.phaseId,
                        uas.updatedTimeStamp,
                        uas.userArtifactSubmissionId,
                        p.name,
                        u.username
                    FROM Artifact a
                    INNER JOIN UserArtifactSubmission uas
                        ON uas.submissionString = a.artifactString
                    INNER JOIN Phase p
                        ON a.phaseId = p.phaseId
                    INNER JOIN User u
                        ON uas.userId = u.userId
                    WHERE a.phaseId = %s''')

    data = (phase_id,)
    sCount = cursor.execute(phase_query, data)
    phaseData = cursor.fetchall()

    cursor.close()

    return render_template('phases.html',  title='Phases', phaseList = phaseList,phaseData=phaseData, data=data, sCount=sCount)

# plot correct submissions by phase
@app.route("/plot_phases", methods=['GET', 'POST'])
@is_logged_in
@is_assessor
def plot_phases():
    cursor = db.connection.cursor()

    successes = []
    labels = []

    # make list of all phases from db
    cursor.execute('SELECT phaseId, name FROM Phase')
    phaseList = cursor.fetchall()

    # iterate through phase list to get count of successes by phase
    for phase in phaseList:
        pID = str(phase.get('phaseId'))
        labels.append(phase.get('name'))
        success_query = ('''SELECT a.phaseId 
                            FROM Artifact a
                            INNER JOIN UserArtifactSubmission uas
                                ON uas.submissionString = a.artifactString
                            INNER JOIN Phase p
                                ON p.phaseId = a.phaseId
                            WHERE p.phaseId = %s'''
        )

        s = cursor.execute(success_query, [pID])
        successes.append(s)
    
    cursor.close()
    
    fig = Figure()
    x = np.arange(len(labels))
    width = 0.35

    maxS = max(successes)
    intsRange = range(0, maxS+1)

    fig, ax = plt.subplots()
    rects1 = ax.bar(x, successes, width)

    ax.set_yticks(intsRange)
    ax.set_ylabel('Correct Submissions')
    ax.set_xlabel('Phases')
    ax.set_title('Correct Submissions by Phase')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    ax.bar_label(rects1, padding=3)

    fig.tight_layout()
    canvas = FigureCanvas(fig)
    output = io.BytesIO()

    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'img/png'
    return response


# Artifact table, login assessor required 
@app.route("/artifactList", methods=['GET', 'POST'])
@is_logged_in
@is_assessor
def artifactList():
    if request.method == 'GET':

        # create cursor
        cur = db.connection.cursor()

        #fetch data
        results = cur.execute("SELECT artifactId, concat('MSEL',phaseId,'-' ,phaseArtifactId) AS msel ,phaseArtifactId , phaseId, userId ,artifactName ,artifactType ,artifactString ,difficulty ,notes FROM Artifact")
        results = cur.fetchall()


        # close connection
        cur.close() 

        return render_template("artifactList.html", results=results)


    return render_template("artifactList.html")

# Assessors Home Page, login Required, assessor or admin role required
@app.route("/generateReport")
@is_logged_in         
@is_assessor
def generateReport():
    cur = db.connection.cursor()
            
    cur.execute('SELECT userId, username FROM User WHERE roleId = 0')
    teamList = cur.fetchall()
        
    # get post from dropdown on team    
    #team_id = request.form.get('dropdown')
    
    return render_template('generateReport.html', title='Generate Reports', teamList=teamList)

# Manage Phases, login admin required
@app.route("/managePhases", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def managePhases():

    form = PhaseManagementForm()
    cursor = db.connection.cursor()

    sessionName = session

    try:
        newPhaseName = form.phaseName.data
        editPhaseName = form.editPhaseName.data
        selectedPhase = request.form.get('phaseSelect')


        if 'createSubmit' in request.form:
            print('create new phase: ' + str(newPhaseName))
            cursor.execute('INSERT INTO Phase (name) VALUES ("'+ str(newPhaseName) + '")')

            # Commit to DB
            db.connection.commit()

        elif 'deleteSubmit' in request.form:
            query = 'DELETE FROM Phase WHERE name = "' + str(selectedPhase) +'";'
            query += "ALTER TABLE Phase AUTO_INCREMENT = 1;"
            print('delete ' + str(selectedPhase))
            cursor.execute(query)

            print(query)
            # Commit to DB
            db.connection.commit()

        elif 'renameSubmit' in request.form:
            print('rename ' + str(selectedPhase) + ' to ' + str(editPhaseName))
            cursor.execute('UPDATE Phase SET name = "' + str(editPhaseName) +'" WHERE name = "' + str(selectedPhase) +'"')

            # Commit to DB
            db.connection.commit()
    except Exception as e:
        print(e)


    cursor.execute('SELECT name FROM Phase order by phaseId asc')
    phaseList = cursor.fetchall()

    form.phaseName.data = ''
    form.editPhaseName.data = ''

    # close connection
    cursor.close()
    #return redirect(url_for('managePhases'))
    return render_template('managePhases.html',  form=form, title='Manage Phases', phases = phaseList)

# Manage teams, login admin required
@app.route("/manageTeams")
@is_logged_in
@is_admin
def manageTeams():

      # create cursor
    cursor = db.connection.cursor()

    # get all teamIds from db
    cursor.execute('SELECT username FROM User WHERE roleId = 0')

    # fetch list of all team data to pass to html
    teamList = cursor.fetchall()

    # close connection
    cursor.close() 


    return render_template('manageTeams.html',  title='Manage Teams', teams=teamList) 

@app.route("/deleteAllTeams")
@is_logged_in
@is_admin
def deleteAllTeams():

    # create cursor
    cursor = db.connection.cursor()

    # get all teamIds from db
    cursor.execute('DELETE FROM User WHERE roleId = 0')

    # Commit to DB
    db.connection.commit()

    # close connection
    cursor.close() 
    flash('You have successfully deleted all of the team accounts!', 'success') 

    return redirect(url_for('manageTeams')) 

@app.route("/deleteAllSubmissions")
@is_logged_in
@is_admin
def deleteAllSubmissions():

    # create cursor
    cursor = db.connection.cursor()

    # get all teamIds from db
    cursor.execute('DELETE FROM UserArtifactSubmission')

    # Commit to DB
    db.connection.commit()

    # close connection
    cursor.close() 
    flash('You have successfully delted all of the team artifact submissions!', 'success') 

    return redirect(url_for('manageTeams'))



# Artifact upload, login admin Required
@app.route("/artifactUpload")
@is_logged_in
@is_admin
def artifactUpload():
    # create cursor
    cursor = db.connection.cursor()

    # get artifacts from db
    cursor.execute("SELECT artifactId, concat('MSEL',phaseId,'-' ,phaseArtifactId) AS msel ,phaseArtifactId , phaseId, userId ,artifactName ,artifactType ,artifactString ,difficulty ,notes FROM Artifact")
    artifacts = cursor.fetchall()

    # close connection
    cursor.close() 


    return render_template('artifactUpload.html',  title='Artifact Upload', artifacts=artifacts)
    

@app.route("/bulkArtifact", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def bulkArtifact():
    form = FileUploadForm()

    if form.validate_on_submit():
        f = form.file.data

        filename = secure_filename(f.filename)

        file_path = os.path.join(filename)

        f.save(file_path)

        col_names = ['name','phaseArtifactId','artifactName', 'artifactType', 'artifactString',  'difficulty', 'notes']
        csvData = pd.read_csv(file_path,header=[0])

        cur = db.connection.cursor()
        userID = session['userId']

        csvColumnList = csvData.columns.tolist()

        sortedTargetColNamesList = sorted(col_names)
        sortedCsvColNamesList = sorted(csvColumnList)

        targetColNamesString = ''.join(sortedTargetColNamesList)
        csvColumnNamesString = ''.join(sortedCsvColNamesList)


        #Check if the columns of the uploaded csv match with the target columns
        if targetColNamesString != csvColumnNamesString:
            flash("Error:  Uploaded CSV doesn't match with: name, phaseArtifactId, artifactName, artifactType, artifactString, difficulty, notes")
            flash("Please try again.")
            return redirect(url_for('artifactUpload'))

        for i, row in csvData.iterrows():
            sql = "INSERT INTO Artifact( userId, phaseId, phaseArtifactId, artifactName, artifactType, artifactString, difficulty, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

            sqlPhase = "SELECT phaseId FROM Phase WHERE name = '""" + row['name'] + "'"
            cur.execute(sqlPhase)
            phaseDict = cur.fetchone()

            value = (str(userID),str(phaseDict['phaseId']),str(row['phaseArtifactId']),str(row['artifactName']), str(row['artifactType']), str(row['artifactString']), str(row['difficulty']), str(row['notes']))

            #ensure deleted indexes will be reused
            resetQuery = "ALTER TABLE Artifact AUTO_INCREMENT = 1;"
            cur.execute(resetQuery)

            db.connection.commit()

            cur.execute(sql, value)

            db.connection.commit()

        
        cur.close()
        
        flash('Artifact List Uploaded!', 'success')

        return redirect(url_for('artifactUpload'))
    

    return render_template('bulkArtifact.html', form=form, title='Upload Artifact List')



@app.route("/individualArtifact", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def individualArtifact():
    form = ArtifactForm()
    
    phaseId = None
    phaseName = None

    cur = db.connection.cursor()
    
    #if form.validate_on_submit():
    if 'submit' in request.form:
        is_validated = form.validate()
        phaseId = form.phaseId.data
        artifactName = form.artifactName.data
        artifactType = form.artifactType.data
        artifactString = form.artifactString.data
        difficulty = form.difficulty.data
        notes = form.notes.data

        #cur = db.connection.cursor()

        #Add a session cookie for the User that way there will be no need to fill out a field for userId
        userID = session['userId']

        #Get the phases currently stored in the database
        phaseName = request.form.get('phaseSelect')

        insertSql = "INSERT INTO Artifact(userId, phaseId, phaseArtifactId, artifactName, artifactType, artifactString, difficulty, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

        cur.execute("SELECT phaseId FROM Phase WHERE name = '" + str(phaseName) +"'")
        
        NEW_phaseId = cur.fetchone()
        NEW_phaseId = NEW_phaseId.get('phaseId')

        sql = "SELECT IFNULL(max(phaseArtifactId)+1,1) as phaseArtifactId FROM Artifact Where phaseId =" + str(NEW_phaseId)
        cur.execute(sql)
        result = cur.fetchone()

        newPhaseArtifactId = result['phaseArtifactId']

        value = (str(userID), str(NEW_phaseId), str(newPhaseArtifactId), artifactName, artifactType, artifactString, difficulty, notes)

        #ensure deleted indexes will be reused
        resetQuery = "ALTER TABLE Artifact AUTO_INCREMENT = 1;"
        cur.execute(resetQuery)

        db.connection.commit()

        cur.execute(insertSql, value)

        db.connection.commit()
        
        #cur.close()
        
        flash('Artifact Uploaded!', 'success')

        return redirect(url_for('artifactUpload'))
    
    phaseSql = "SELECT name FROM Phase "

    if phaseId is None:
        phaseSql += "ORDER BY phaseId asc"
    else:
        phaseSql += "ORDER BY name ='"+str(phaseId)+"' desc, phaseId asc"

    cur.execute(phaseSql)
    phaseList = cur.fetchall()
    
    db.connection.commit()
    
    cur.close()
    
    return render_template('individualArtifact.html', form=form, title='Upload Individual Artifact', phases = phaseList)

@app.route("/editArtifact", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def editArtifact():
    form = EditArtifactForm()

    artifactList = None
    phaseList = None
    phaseName = None

    cur = db.connection.cursor()

    if 'selectSubmit' in request.form:
        currentlySelectedMSEL = request.form.get('artifactSelect')

        sql = """SELECT a.artifactId,a.phaseArtifactId, p.name, a.artifactName, a.artifactType, a.artifactString, a.difficulty, a.notes FROM Artifact a
                JOIN Phase p ON a.phaseId = p.phaseId
                WHERE concat('MSEL',a.phaseId,'-' ,a.phaseArtifactId) = '""" + str(currentlySelectedMSEL) + """'
                LIMIT 1"""

        cur.execute(sql)
        result = cur.fetchone()

        artifactId = result['artifactId']
        phaseArtifactId = result['phaseArtifactId']
        phaseName = result['name']
        artifactName = result['artifactName']
        artifactType = result['artifactType']
        artifactString = result['artifactString']
        difficulty = result['difficulty']
        notes = result['notes']

        form.artifactId.data = artifactId
        form.phaseArtifactId.data = phaseArtifactId
        form.phaseName.data = phaseName
        form.artifactName.data = artifactName
        form.artifactType.data = artifactType
        form.artifactString.data = artifactString
        form.difficulty.data = difficulty
        form.notes.data = notes


    elif 'submit' in request.form:
        is_validated = form.validate()
        artifactId = form.artifactId.data
        phaseArtifactId = form.phaseArtifactId.data
        phaseName = form.phaseName.data
        artifactName = form.artifactName.data
        artifactType = form.artifactType.data
        artifactString = form.artifactString.data
        difficulty = form.difficulty.data
        notes = form.notes.data

        currentlySelectedPhaseName = request.form.get('phaseSelect')

        sql = """(SELECT phaseId FROM Phase WHERE name = '""" + str(currentlySelectedPhaseName) +"')"
        cur.execute(sql)
        result = cur.fetchone()

        currentlySelectedPhaseId = result['phaseId']

        #make sure there's not a phaseId + phaseArtifactId UNIQUE conflict:
        sql = "SELECT * FROM Artifact where phaseId = "+str(currentlySelectedPhaseId)+" AND phaseArtifactId = " + str(phaseArtifactId)
        cur.execute(sql)
        result = cur.fetchone()

        if result is not None:
            flash('phaseArtifactId+phaseId combination already exists - please choose a different combination')
        else:
            sqlUpdate = """UPDATE Artifact
                        SET phaseArtifactId = """+str(phaseArtifactId)+", phaseId = "+str(currentlySelectedPhaseId)+",artifactName = '" + str(artifactName) + "',artifactType = '" + str(artifactType) + "',artifactString = '" + str(artifactString) + "' ,difficulty = '" + str(difficulty) + "' ,notes = '" + str(notes) + """'
                        WHERE artifactId = """ + str(artifactId)

            print(sqlUpdate)
            cur.execute(sqlUpdate)

    phaseSql = "SELECT name FROM Phase "

    if phaseName is None:
        phaseSql += "ORDER BY phaseId asc"
    else:
        phaseSql += "ORDER BY name ='"+str(phaseName)+"' desc, phaseId asc"

    cur.execute(phaseSql)
    phaseList = cur.fetchall()

        #Commit to DB
    db.connection.commit()

    selectedArtifact = request.form.get('artifactSelect')
    sql = "SELECT concat('MSEL',phaseId,'-' ,phaseArtifactId) AS msel  FROM Artifact"

    if selectedArtifact is None:
        sql+=" ORDER BY phaseId, phaseArtifactId asc"
    else:
        selectedPhaseArtifactId = selectedArtifact.split('_')[0].split('-')[1]
        selectedPhaseId = selectedArtifact.split('-')[0].split('MSEL')[1]
        sql+=" ORDER BY artifactId = (SELECT artifactId from Artifact WHERE phaseArtifactId = "+str(selectedPhaseArtifactId)+" AND phaseId = "+str(selectedPhaseId)+") desc, phaseId, phaseArtifactId asc "

    cur.execute(sql)
    artifactList = cur.fetchall()

    cur.close()

    return render_template('editArtifact.html', form=form, title='Edit an Artifact',artifacts=artifactList, phases = phaseList)
@app.route("/deleteArtifactList")
@is_logged_in
@is_admin
def deleteArtifactList():
    # create cursor
    cursor = db.connection.cursor()

    # get all artifactIds from db
    cursor.execute('DELETE FROM Artifact')

    # Commit to DB
    db.connection.commit()

    # close connection
    cursor.close() 
    flash('You have successfully deleted the artifact list!', 'success') 

    return redirect(url_for('artifactUpload')) 

# admin register, no login required
@app.route("/admin/register", methods=['GET', 'POST'])
def registerAdmin():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        role = ADMIN

        # Create cursor
        cur = db.connection.cursor()

        #check if username already exists
        results = cur.execute("SELECT * FROM User WHERE username = %s", [username])
        if results > 0:
            error = 'username already in use, choose a different one'
            # Close connection
            cur.close()
            return render_template('register.html', form=form, title='Register Admin', error=error)


        cur.execute("INSERT INTO User(username, passwordHash, roleId) VALUES(%s, %s, %s)", (username, password, int(role)))

        # Commit to DB
        db.connection.commit()

        # Close connection
        cur.close()

        flash('Admin account created!', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form, title='Register Admin')


# assessor register, no login required
@app.route("/assessor/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        role = ASSESSOR

        # Create cursor
        cur = db.connection.cursor()

        #check if username already exists
        results = cur.execute("SELECT * FROM User WHERE username = %s", [username])
        if results > 0:
            error = 'username already in use, choose a different one'
            # Close connection
            cur.close()
            return render_template('register.html', form=form, title='Register Assessor', error=error)

        cur.execute("INSERT INTO User(username, passwordHash, roleId) VALUES(%s, %s, %s)", (username, password, int(role)))

        # Commit to DB
        db.connection.commit()

        # Close connection
        cur.close()

        flash('Assessor account created!', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form, title='Register Assessor')

# bulk team register, login admin required
@app.route("/team/register/bulk", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def registerTeamBulk():
    form = BulkRegisterForm()
    if form.validate_on_submit():
        howMany = form.howMany.data #number of teams to register
        role = TEAM
        name = 'Team'
        password = 'password123'
        defaultPassword = sha256_crypt.encrypt(str(password))
        addedUsernames = []
        flag = 0

        # Create cursor
        cur = db.connection.cursor()

        value = 1 
        for i in range(howMany):
            # check if username already exists
            while flag == 0:
                username = name+str(value)
                results = cur.execute("SELECT * FROM User WHERE username = %s", [username])
                if results > 0:
                    value = value + 1
                else:
                    flag = 1

            cur.execute("INSERT INTO User(username, passwordHash, roleId) VALUES(%s, %s, %s)", (username, defaultPassword, int(role)))
            addedUsernames.append(username)
            flag = 0

        # Commit to DB
        db.connection.commit() 

        # Close connection
        cur.close()

        flash('Team accounts created!', 'success')


        return render_template("registerSuccess.html", newUsers=addedUsernames, defaultPassword=password)

    return render_template("bulkRegister.html", form=form, title="Register Teams")

# team register, login admin required
@app.route("/team/register", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def registerTeam():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        role = TEAM

        # Create cursor
        cur = db.connection.cursor()

        #check if username already exists
        results = cur.execute("SELECT * FROM User WHERE username = %s", [username])
        if results > 0:
            error = 'username already in use, choose a different one'
            # Close connection
            cur.close()
            return render_template('register.html', form=form, title='Register Team', error=error)


        cur.execute("INSERT INTO User(username, passwordHash, roleId) VALUES(%s, %s, %s)", (username, password, int(role)))

        # Commit to DB
        db.connection.commit()

        # Close connection
        cur.close()

        flash('Team account created!', 'success')

        return redirect(url_for('manageTeams'))
    return render_template('register.html', form=form, title='Register Team')


# Login page
@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
       
        # Get form fields
        username = request.form['username']
        password_canidate = request.form['password']

        # Create cursor
        cur = db.connection.cursor()

        results = cur.execute("SELECT * FROM User WHERE username = %s", [username])

        if results > 0:
            
            # Get stored hash
            data = cur.fetchone()
            password = data['passwordHash']
            role = data['roleId']
            userId = data['userId']

            # Compare Passwords
            if sha256_crypt.verify(password_canidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['userId'] = userId
                session['role'] = role

                #assign role names to display on profile
                if role == 0:
                    session['rolename'] = 'Team'
                    flash('You have been logged in!', 'success')
                    return redirect(url_for('playerhome'))
                elif role == 1:
                    session['rolename'] = 'Assessor'
                    flash('You have been logged in!', 'success')
                    return redirect(url_for('assessorhome'))
                elif role == 2:
                    session['rolename'] = 'Admin'
                    flash('You have been logged in!', 'success')
                    return redirect(url_for('admin'))
                else:
                    session['rolename'] = 'Unknown'
                    flash('You have been logged in!', 'success')
                    return redirect(url_for('/'))


        

            else:

                error = 'Invalid Password'
                return render_template('login.html', form=form, title='Login', error=error)

            # Close connection
            cur.close()

        else:
            error = 'Invalid Username'
            return render_template('login.html', form=form, title='Login', error=error)

    return render_template('login.html', form=form, title='Login')

# Logout, login required
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash('You have been successfully logged out!', 'success')
    return redirect(url_for('login'))

# Profile page, login Required
@app.route("/profile", methods=['GET', 'POST'])
@is_logged_in
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
       
        # Get form fields
        oldPassword_canidate = form.oldPassword.data
        newPassword = sha256_crypt.encrypt(str(form.newPassword.data))

        #get username of logged in user
        username = session['username']

        # Create cursor
        cur = db.connection.cursor()

        results = cur.execute("SELECT * FROM User WHERE username = %s", [username])
      

        if results > 0:
            
            # Get stored hash
            data = cur.fetchone()
            oldPassword = data['passwordHash']

            # Compare Passwords
            if sha256_crypt.verify(oldPassword_canidate, oldPassword):
                # Passed
                cur.execute("UPDATE User SET passwordHash = %s WHERE username = %s ", [newPassword, username])
                # Commit to DB
                db.connection.commit()
                flash('You have successfully changed your password!', 'success')    

            else:
                error = 'Original Password entered is incorrect'
                return render_template('profile.html', form=form, title='Profile', error=error)

            # Close connection
            cur.close()


    return render_template('profile.html', form=form, title='Profile')

@app.route("/deleteAccount")
@is_logged_in
@is_admin
def deleteAccount():

    #get username of logged in user
    username = session['username']

    # create cursor
    cursor = db.connection.cursor()

    #Delete the user
    cursor.execute("DELETE FROM User WHERE username = %s", [username])

    # Commit to DB
    db.connection.commit()

    # close connection
    cursor.close() 
    flash('You have successfully deleted your account!', 'success') 

    return redirect(url_for('logout')) 

# New user table after bulk team register, login admin required
@app.route("/success", methods=['GET', 'POST'])
@is_logged_in
@is_admin
def success():
    return render_template("registerSuccess.html")


@app.route("/downloadCSV")
@is_logged_in
#@is_admin
@is_assessor
def downloadCSV():
    cur = db.connection.cursor()

    sql =   """SELECT a.artifactId, a.userId, p.name, a.phaseArtifactId, a.artifactName, a.artifactType, a.artifactString, a.difficulty, a.notes 
            FROM Artifact a
            JOIN Phase p ON p.phaseId = a.phaseId"""

    cur.execute(sql)
    result = cur.fetchall()
        
    output = io.StringIO()
    writer = csv.writer(output)
        
    col_names = ['name','phaseArtifactId', 'artifactName', 'artifactType', 'artifactString', 'difficulty', 'notes']
    writer.writerow(col_names)
        
    for row in result:
        columns = [str(row['name']), str(row['phaseArtifactId']), str(row['artifactName']), str(row['artifactType']), str(row['artifactString']), str(row['difficulty']), str(row['notes'])]
        writer.writerow(columns)
            
    output.seek(0)
    
    cur.close()
        
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=ArtifactList.csv"})

@app.route("/downloadTeamSubmissions")
@is_logged_in
#@is_admin
@is_assessor
def downloadTeamSubmissions():
    cur = db.connection.cursor()
        
    cur.execute("SELECT * FROM UserArtifactSubmission")
    result = cur.fetchall()
        
    output = io.StringIO()
    writer = csv.writer(output)
        
    col_names = ['userArtifactSubmissionId', 'userId', 'submissionString', 'updatedTimeStamp']
    writer.writerow(col_names)
        
    for row in result:
        columns = [str(row['userArtifactSubmissionId']), str(row['userId']), str(row['submissionString']), str(row['updatedTimeStamp'])]
        writer.writerow(columns)
            
    output.seek(0)
    
    cur.close()
        
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=TeamSubmissions.csv"})
    
@app.route("/downloadByTeam", methods=['GET', 'POST'])
@is_logged_in
#@is_admin
@is_assessor
def downloadByTeam():
    if request.method == 'POST':

        cur = db.connection.cursor()

        # get post from dropdown on team    
        team_id = request.form.get('dropdown')
        
        
        cur.execute("SELECT * FROM UserArtifactSubmission WHERE userId = '" + str(team_id) + "'")
        result = cur.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        col_names = ['userArtifactSubmissionId', 'userId', 'submissionString', 'updatedTimeStamp']
        writer.writerow(col_names)
        
        for row in result:
            columns = [str(row['userArtifactSubmissionId']), str(row['userId']), str(row['submissionString']), str(row['updatedTimeStamp'])]
            writer.writerow(columns)
            
        output.seek(0)
    
        cur.close()

        return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=SelectedTeamSubmissions.csv"})
    
    

# Run Server
if __name__ == '__main__':
    app.run(debug=True)
    #flask run is the command to run it
