from flask import Flask, render_template,request,jsonify,session,flash,redirect
import mysql.connector
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime as dl
import os
import secrets
from PIL import Image
#from modules.py import content2
import pathlib
from flask import Flask, render_template, request
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import pandas as pd
import pytube
from pytube import YouTube
import bcrypt
import base64
from PIL import Image
import logging
import mimetypes
from mysql.connector import Error, errorcode







app = Flask(__name__)
app.secret_key = '0000'
app.config['SESSION_COOKIE_SECURE'] = True

#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Set session timeout to 30 minutes

basedir = os.path.abspath(os.path.dirname(__file__))

# Configure the upload folder path
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'images')



def generate_random_code():
    code = ''.join(str(random.randint(0, 9)) for _ in range(6))
    return code

email = "kariuki12nicholas@gmail.com"
password = "kfpszcrbpqxvqjyw"
subject="INJUSTICE CODES"


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def is_valid_password(password, min_length):
   return len(password) >= min_length



def connect_to_database():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="0000",
            database="details"
        )
        return mydb
    except mysql.connector.Error as err:
        if err.errno == errorcode.CR_CONNECTION_ERROR:
            # Connection lost, attempt to reconnect
            print("Lost connection to MySQL server. Reconnecting...")
            return connect_to_database()
        else:
            raise 
mydb = connect_to_database()
mycursor = mydb.cursor()


    
#LOGING CODES
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            User_email = request.form['email']
            password = request.form['password']
            
            # Check user_details table
            sql = "SELECT password, username FROM user_details WHERE email=%s"
            mycursor.execute(sql, (User_email,))
            user_info = mycursor.fetchall()
       
            for result in user_info:
                stored_hashed_password = result[0]
                password_check = bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8'))
                
                if password_check:
                    success_msg = f"Welcome, {result[1]}!"
                    session['profile_email'] = User_email
                    session.permanent = True 
                    userdata= get_user_desc(User_email)
                    return render_template('s-home page.html', success_msg=success_msg,userdata=userdata)
                    
                   
        
        except Exception as e:
            error_msg = f"Error: {e}"
            app.logger.error(f"Error during login: {e}")
            return render_template('s-home page.html', error_msg=error_msg)
        
        # If user not found in user_details table, check admin_details table
        sql = "SELECT password, username FROM admin_details WHERE email=%s"
        mycursor.execute(sql, (User_email,))
        admin_info = mycursor.fetchall()
        
        for result in admin_info:
            stored_hashed_password = result[0]
            password_check = bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8'))

            if password_check:
                msg = f'Welcome, {result[1]}!'
                userdata= get_user_desc(User_email)
                return render_template('admin.html', msg=msg,userdata=userdata)

        # If neither user nor admin found, display error message
        error_msg = "Wrong password or email!"
    
        return render_template('s-login.html', error_msg=error_msg)
    
      
   
    return render_template('s-login.html')


def get_user_desc(user_email):

    sql = "SELECT phone, username, email, intrest, Bio, profile_pic FROM user_details WHERE email=%s"
    mycursor.execute(sql, (user_email,))
    userinfo = mycursor.fetchone()
    
    if userinfo:
        data_accumulated = {
            "Phone": userinfo[0],
            "Username": userinfo[1],
            "Email": userinfo[2],
            "Interest": userinfo[3],
            "Bio": userinfo[4],
        }
        if userinfo[5] is not None:
            data_accumulated["profile"] = encode_image(userinfo[5])
        else:
            image_path = "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\images\\bald_placeholder.jpg"
            data_accumulated["profile"] = encode_image(image_path)
        userdata = [data_accumulated]
    else:
        data_accumulated = {
            "Phone": "None",
            "Username": "None",
            "Email": "None@gmail.com",
            "Interest": "None",
            "Bio": "None",
        }
        image_path = "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\images\\bald_placeholder.jpg"
        data_accumulated["profile"] = encode_image(image_path)
        userdata = [data_accumulated]
         
    if isinstance(userdata, list) and userdata:
        userinfo = userdata
    else:
        userinfo = None

    return userinfo
    

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            user_name = request.form['name']
            u_email = request.form['email']
            u_password = request.form['password']
            confirmpassword = request.form['confirmpassword']

            # Fetch existing user details
            mycursor.execute("SELECT email, username FROM user_details")
            my_info = mycursor.fetchall()
            
            # Check if email already exists
            if any(u_email == check[0] for check in my_info):
                error_msg = "Email already registered, enter a valid email!"
                return render_template('s-login.html', error_msg=error_msg)
            
            # Check if username already exists
            if any(user_name == check[1] for check in my_info):
                error_msg = "Username already occupied, kindly enter another Username!"
                return render_template('s-login.html', error_msg=error_msg)
            
            # Check if the password is valid
            if not is_valid_password(u_password, 6):
                Warning_msg = "Password too short, set at least 6 characters"
                return render_template('s-login.html',warning_msg=Warning_msg )
            
            # Check if passwords match
            if u_password != confirmpassword:
                Warning_msg = "Passwords do not match, please try again"
                return render_template('s-login.html',warning_msg=Warning_msg)

            # All checks passed, proceed to email verification
            random_code = generate_random_code()
            now = dl.datetime.now()
            email_message = f"Enter this code {random_code} to verify your email on {now.strftime('%Y-%m-%d %H:%M:%S')}"
            send_codes(random_code, u_email, email_message)
            
            # Store random code and user details in the session
            session['random_code'] = random_code
            session['user_name'] = user_name
            session['u_email'] = u_email
            session['u_password'] = u_password
            help_msg="Enter 6 digit codes sent to your email!"

            return render_template('email_confirm.html',help_msg=help_msg)
        
        else:
            return render_template('s-login.html',error_msg="Error signinng up!!")
        
    except Exception as e:
        error_msg = "Error: " + str(e)
        return render_template('s-login.html', error_msg=error_msg)
   
      
       

@app.route('/preview', methods=['POST'])
def preview():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Form validation
        if not title or not content:
            logging.debug("Title or content is empty!")
            return render_template('admin.html', msg="Title or content is empty!")

        try:
            now = dl.datetime.now()
            date = now.strftime("%Y-%m-%d %H:%M:%S")

            # Handle image upload
            if 'image' in request.files and 'image2' in request.files and 'image3' in request.files:
                image1 = request.files['image']
                image2 = request.files['image2']
                image3 = request.files['image3']
                image4 = request.files.get('image4')  # Use get to handle cases where image4 might not be provided

                filenames = []
                for img in [image1, image2, image3, image4]:
                    if img and img.filename != '':
                        filename = secure_filename(img.filename)
                        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        img.save(image_path)
                        logging.debug(f"Saved file: {image_path}")
                        
                        if allowed_file(filename, image_path):
                            filenames.append(image_path)
                            logging.debug(f"File format allowed: {image_path}")
                        else:
                            os.remove(image_path)
                            filenames.append(None)
                            logging.debug(f"File format not allowed, removed: {image_path}")
                    else:
                        filenames.append(None)
                        logging.debug("No file uploaded or filename is empty")
            else:
                filenames = [None, None, None, None] 
                logging.debug("Required images are not uploaded")

            # Database connection
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="0000",
                database="details"
            )
            mycursor = mydb.cursor()

            # Insert data into the main table
            sql = "INSERT INTO daily_content (title, contents, date) VALUES (%s, %s, %s)"
            val = (title, content, date)
            mycursor.execute(sql, val)
            mydb.commit()
            logging.debug("Inserted data into daily_content table")

            # Get the last inserted ID
            content_id = mycursor.lastrowid

            # Insert image paths into the daily_content_images table
            for image_path in filenames:
                if image_path:
                    sql = "INSERT INTO daily_content_images (content_id, image_path) VALUES (%s, %s)"
                    val = (content_id, image_path)
                    mycursor.execute(sql, val)
                    mydb.commit()
                    logging.debug(f"Inserted image path into daily_content_images table: {image_path}")

            success_msg = "Data uploaded successfully with images" if any(filenames) else "Data uploaded successfully, no images"

            return render_template('admin.html', success_msg=success_msg)

        except Exception as e:
            logging.error(f"Error: {e}")
            return render_template('admin.html', error_msg=f"Error: {e}")

        finally:
        
                logging.debug("Database connection closed")

    logging.debug("Invalid request method")
    return render_template('admin.html', error_msg="Invalid request method")


@app.route('/load_content', methods=['GET'])
def load_content():
    """Fetches and processes daily content from the database in chunks."""
    chunk_size = int(request.args.get('chunk_size', 10))
    offset = int(request.args.get('offset', 0))

    try:
        mydb = connect_to_database()  # Establish database connection
        mycursor = mydb.cursor()  # Create cursor

        mycursor.execute("SELECT * FROM daily_content ORDER BY date DESC LIMIT %s OFFSET %s", (chunk_size, offset))
        rows = mycursor.fetchall()
        content_list = []
        for row in rows:
            time=format_date(row[3])
            content_item = {
                'id': row[0],
                'title': row[1],
                'date':time, 
                'news': row[2],
            }
            content_list.append(content_item)

        return jsonify(content_list)

    except mysql.connector.Error as err:
        return f"Database error: {err}", 500

@app.route('/load_media/<int:content_id>', methods=['GET'])
def load_media(content_id):
    """Fetches images and videos related to the specified content item."""
    try:
        mydb = connect_to_database()  # Establish database connection
        mycursor = mydb.cursor()  # Create cursor

        mycursor.execute("SELECT * FROM daily_content_images WHERE content_id = %s", (content_id,))
        media_files = mycursor.fetchall()

        media_list = []
        for media_file in media_files:
            file_path = media_file[2]
            if file_path:
                file_extension = os.path.splitext(file_path)[-1].lower()

                if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    with open(file_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                    media_list.append({
                        'type': 'image',
                        'content': f'data:image/{file_extension[1:]};base64,{encoded_image}'
                    })
                elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
                    # Encode video file to base64
                    encoded_video = encode_video_to_base64(file_path)
                    media_list.append({
                        'type': 'video',
                        'content': f'data:video/{file_extension[1:]};base64,{encoded_video}'
                    })
                else:
                    continue  # Unsupported file type
            else:
                continue  # Empty file path


        return jsonify(media_list)
    
    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({'error': 'Failed to load media'}), 500

def encode_video_to_base64(video_path):
    """Encodes a video file into a base64 string."""
    with open(video_path, "rb") as video_file:
        encoded_video = base64.b64encode(video_file.read()).decode("utf-8")
    return encoded_video


@app.route('/')
def index():
    return render_template('s-login.html')


logging.basicConfig(level=logging.DEBUG)

# Define supported file formats
ALLOWED_IMAGE_EXTENSIONS = {'jpeg', 'jpg', 'png', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS)

def allowed_file(filename, file_path):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return True
    elif ext in ALLOWED_IMAGE_EXTENSIONS:
        try:
            with Image.open(file_path) as img:
                return img.format.lower() in ALLOWED_IMAGE_EXTENSIONS
        except (IOError, SyntaxError):
            return False
    return False



def send_codes(random_code, addr,email_message):
    now = dl.datetime.now()
    email_message = f"Enter this code {random_code} to verify your email on {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    message = MIMEMultipart()
    message['From'] = email
    message['To'] = addr
    message['Subject'] = "INJUSTICE CODES"

    message.attach(MIMEText(email_message, 'plain'))

    connection = smtplib.SMTP("smtp.gmail.com", 587)
    connection.starttls()
    connection.login(email, password)
    connection.sendmail(email, addr, message.as_string())
    connection.close()
    
@app.route('/verify', methods=['GET', 'POST'])
def verify():

    random_code = session.get('random_code')
    input_code = request.form['input_code']
    if random_code == input_code:
        try:
            user_name = session.get('user_name')
            u_password = session.get('u_password')
            hashed_password = hash_password(u_password)
            u_email = session.get('u_email')
            min_length = 6
            password = u_password
            if is_valid_password(password, min_length):
                sql = "INSERT INTO user_details (username, email, password) VALUES (%s, %s,%s)"
                val = (user_name, u_email, hashed_password)
                mycursor.execute(sql, val)
                mydb.commit()
                return render_template('s-login.html', success_msg="ACCOUNT SUCCESFULLY CREATED, login now! ")
            else:
                return render_template('s-login.html', warning_msg= f" password too short, set atleast 6 characters")
        
                
        except Exception as e:
            return render_template('s-login.html', error_msg= f"error:{e}")
        

    else:
        return render_template('s-login.html', error_msg="Codes don't match, please try again")
    
   
    

@app.route('/password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('recovery_email.html')

@app.route('/get_email', methods=['GET', 'POST'])
def password_recovery():
    if request.method == 'POST':
        recovery_email=request.form['recovery_email']
        try:
            mycursor.execute("SELECT email FROM user_details")
            my_info = mycursor.fetchall()
            found=False
            for personal_info in my_info:
                if personal_info[0]== recovery_email :
                    found=True
                    addr=recovery_email
                    random_code2 = generate_random_code()
                    now = dl.datetime.now()
                    email_message = f"Enter this code {random_code2} to verify your email on ,{now.strftime('%Y-%m-%d %H:%M:%S')}"
                    send_codes(random_code2, addr,email_message) 
                    session['recovery_email']=recovery_email
                    session['random_code2']=random_code2
                    return render_template('forgot_password.html', help_msg='Enter 6-digit code sent to your email!')
                else:
                   error_msg="emails not registered, kindly enter registered email or signup!"   
                
            if not found:
                error_msg= "Email not registerd!!"
            
    
        except Exception as e:
            error_msg=f"ERROR: {e}"
               

    return render_template('recovery_email.html', error_msg=error_msg )

@app.route('/verify_code', methods=['GET', 'POST'])
def verifying_codes():
    error_msg = ""
    help_msg = ""
    if request.method == 'POST':
        input_recovery_code = request.form['input_recovery_code']
        if input_recovery_code is None:
            error_msg = "Error: 'input_recovery_code' field is missing from the form data", 400
        else:
            random_code2 = session.get('random_code2')
            
            if input_recovery_code == random_code2:
                recovery_email = session.get('recovery_email')
                help_msg = f"Enter your new password for, {recovery_email}"
                return render_template('password_change.html', help_msg=help_msg)
            else:
                error_msg = "Invalid recovery code. Confirm the code and try again."
                
            
    return render_template('forgot_password.html', error_msg=error_msg)

@app.route('/password_saving', methods=['GET', 'POST'])
def saving_password():
    error_msg=""
    warning_msg=""
    if request.method == 'POST':
        recovery_password = request.form['recovery_password']
        recovery_confirmpassword = request.form['recovery_confirmpassword']
        recovery_email = session.get('recovery_email')
        if recovery_password is None or recovery_confirmpassword is None:
            error_msg = "Session data is missing. Password reset cannot be completed."
        else:
            if recovery_password == recovery_confirmpassword:
                try:
                    hashed_password = hash_password(recovery_password)
                    sql = "UPDATE user_details SET password = %s WHERE email = %s"
                    val = (hashed_password, recovery_email)
                    mycursor.execute(sql, val)
                    mydb.commit()
                    success_msg = f"Password successfully changed for, {recovery_email}"
                    return render_template('s-login.html', success_msg=success_msg)
                except Exception as e:
                    error_msg = "An error occurred while changing password,kindly try again"
            else:
                 warning_msg="Password don't match!!, kindly try again,"       
    if error_msg:
        error_msg=error_msg
    elif warning_msg:
        warning_msg=warning_msg
    else:
        None
                      
    return render_template('password_change.html', warning_msg=warning_msg,error_msg=error_msg)

@app.route('/more', methods=['GET','POST'])    
def update():
    
    return render_template('l_style.html')

@app.route('/camera_more', methods=['GET','POST'])    
def camera_page():
    return render_template('s-camera.html')

@app.route('/download_more', methods=['GET','POST'])    
def download_page():
    return render_template('y-streams.html')

@app.route('/profile_more', methods=['GET', 'POST'])
def get_profile():
    return render_template("profile.html")




@app.route('/profile', methods=['GET', 'POST'])
def up_profile():
    user_data = profile()
    if isinstance(user_data, list) and user_data:
        userinfo = user_data[0]
    else:
        userinfo = None
    return render_template("profile.html", userinfo=userinfo)



#downloading from youtube
@app.route('/streams', methods=['GET', 'POST'])  
def get_streams():
    try:
        if 'link' in request.form and request.form['link']:
            link = request.form['link']
            session['link']=link
            yt = pytube.YouTube(link)
            streams = yt.streams.all()
            help_msg = "Choose file format to download,"
            info = f"""FILE INFO:
            Title: {yt.title},  \t
            Author: {yt.author},  \n\n
            Description: {yt.description},  \t
            Caption: {yt.captions},  \n\n
            Views: {yt.views:,}"""
            session['info']=info
            return render_template('download.html', help_msg=help_msg, streams=streams,info=info)
        else:
            error_msg="NO URL ENERED, kindly enter url"   
            return render_template('y-streams.html', error_sg=error_msg )
       
    except Exception as e:
        error_msg = f"ERROR: {e}"
        return render_template('y-streams.html', error_msg=error_msg, )
       
        
@app.route('/download', methods=['POST'])
def download():
    try:
        if request.method == 'POST':
            link = session.get('link')
            selected_stream = request.form['option']  
            
            yt = pytube.YouTube(link)
            stream = yt.streams.get_by_itag(selected_stream)
            
            if stream:
                upload_folder = "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\pytube"
                filename = f"{yt.title}.{stream.mime_type.split('/')[1]}"
                file_path = os.path.join(upload_folder, filename)
                
                stream.download(file_path)
                success_msg = f"Download complete: {yt.title}, {yt.description}"
                yt = pytube.YouTube(link)
                streams = yt.streams.all()
                info = session.get('info')
                return render_template('download.html', streams=streams, info=info, success_msg=success_msg)
            else:
                error_msg = "Selected stream not available for download."
                return render_template('download.html', error_msg=error_msg)
    except Exception as e:
        error_msg = f"ERROR: {e}"
        return render_template('download.html', error_msg=error_msg)


    
@app.route('/download-progress')
def download_progress():
    try:
        progress = 100  
        return jsonify({'progress': progress})
    except Exception as e:
        return jsonify({'error': str(e)})   
        
@app.route('/capture', methods=['POST'])
def capture():
    now = dl.datetime.now()
    image = request.files['image']
    image_data= image
    username=session.get('username')
    filename = f"image{username}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    image_data = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_data)
     
    error_msg= 'Image captured successfully!'
    return error_msg
    
"""    
upload_folder = "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\pytube"
now = dl.datetime.now()
date = now.strftime("%Y-%m-%d %H:%M:%S")
random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# Combine date, random string, and file extension
filename = f"{random_string}.{stream.mime_type}"

file_path = os.path.join(upload_folder, filename)
stream.download(file_path)    
"""


logging.basicConfig(level=logging.DEBUG)
@app.route('/update_profile', methods=['POST'])
def get_loaded_profile():
    user_data = load_profile()

    userinfo = None
    success_msg = ''

    if isinstance(user_data, list) and user_data:
        userinfo = user_data[0]
        if len(user_data) > 1 and user_data[1]:
            success_msg = "Profile updated successfully!"
    elif isinstance(user_data, str):
        success_msg = user_data
    else:
        userinfo = None

    return render_template('profile.html', userinfo=userinfo, success_msg=success_msg)


     
def load_profile():
    error_msg = ""
    success_msg = ""
    userinfo = ""

    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="0000",
            database="details"
        )
        mycursor = mydb.cursor()

        profile_email = session.get('profile_email')
        if not profile_email:
            logging.debug("User not logged in.")
            error_msg="User not logged in."

        country = request.form.get('country')
        phone = request.form.get('phone')
        intrests = request.form.get('intrests')
        dob = request.form.get('birthdate')
        gender = request.form.get('gender')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')
        bio = request.form.get('bio')

        logging.debug(f"Received data - country: {country}, phone: {phone}, intrests: {intrests}, dob: {dob}, gender: {gender}, city: {city}, state: {state}, postal_code: {postal_code}, bio: {bio}")

        profile_pic = request.files.get('profile_pic')
        profile_pic_path = None
        if profile_pic and profile_pic.filename != '':
            filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_pic.save(profile_pic_path)
            logging.debug(f"Saved file: {profile_pic_path}")

        sql = "UPDATE user_details SET "
        fields = []
        values = []

    
        if country:
            fields.append("country=%s")
            values.append(country)
        if phone:
            fields.append("phone=%s")
            values.append(phone)
        if intrests:
            fields.append("intrest=%s")
            values.append(intrests)
        if dob:
            fields.append("birthdate=%s")
            values.append(dob)
        if gender:
            fields.append("gender=%s")
            values.append(gender)
        if city:
            fields.append("city=%s")
            values.append(city)
        if state:
            fields.append("state=%s")
            values.append(state)
        if postal_code:
            fields.append("postal_code=%s")
            values.append(postal_code)
        if bio:
            fields.append("bio=%s")
            values.append(bio)
        if profile_pic_path:
            fields.append("profile_pic=%s")
            values.append(profile_pic_path)

        if not fields:
            logging.debug("No fields to update.")
            error_msg="No fields to update."

        sql += ", ".join(fields) + " WHERE email=%s"
        values.append(profile_email)

        mycursor.execute(sql, tuple(values))
        mydb.commit()
        
        success_msg="Profile updated successfully." 
       
        userinfo = profile() 
        userinfo += success_msg
        return userinfo

    except mysql.connector.Error as db_err:
        logging.error(f"Database error: {db_err}")
        error_msg= ("Database error."), 500
    except Exception as e:
        logging.error(f"Error updating profile: {e}")
        error_msg= "Error updating profile!!"
   
    return error_msg


def profile():
    profile_email = session.get('profile_email')
    if not profile_email:
        return None

    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="0000",
            database="details"
        )
        mycursor = mydb.cursor()

        sql = "SELECT phone, username, email,intrest, birthdate, gender, address, city, state, postal_code, country, Bio, profile_pic FROM user_details WHERE email=%s"
        mycursor.execute(sql, (profile_email,))
        userinfo = mycursor.fetchone()
        
        if userinfo:
            data_accumulated = {
                "Phone": userinfo[0],
                "Username": userinfo[1],
                "Email": userinfo[2],
                "Interest": userinfo[3],
                "Birthdate": userinfo[4],
                "Gender": userinfo[5],
                "Address": userinfo[6],
                "City": userinfo[7],
                "State": userinfo[8],
                "PostalCode": userinfo[9],
                "Country": userinfo[10],
                "Bio": userinfo[11],
            }
            if profile is not None:
                data_accumulated["profile"]=encode_image(userinfo[12])
            userdata = [data_accumulated]
            return userdata
        else:
            error_msg="Error while fetching data."
            return error_msg
    

    except mysql.connector.Error as err:
        error_msg= (f"Error: {err}")
    
    return error_msg
 
@app.route('/upload_profile_pic', methods=['GET'])
def get_uploaded_profile_pic():
    profile_pic=upload_profile_pic()
    return profile_pic



def upload_profile_pic():
    profile_email = session.get('profile_email')
    if not profile_email:
        return jsonify(message="User not logged in."), 403
    
    try:

        sql = "SELECT profile_pic FROM user_details WHERE email=%s"
        mycursor.execute(sql, (profile_email,))
        userinfo = mycursor.fetchone()
        if userinfo and userinfo[0]:
            file_path = userinfo[0]
            if os.path.isfile(file_path):
                file_extension = os.path.splitext(file_path)[-1].lower()
                with open(file_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                return jsonify([{
                    'type': 'image',
                    'content': f'data:image/{file_extension[1:]};base64,{encoded_image}'
                }])
        return jsonify(message="No profile picture found."), 404
    
    except mysql.connector.Error as db_err:
        logging.error(f"Database error: {db_err}")
        return jsonify(message="Database error."), 500
    except Exception as e:
        logging.error(f"Error retrieving profile picture: {e}")
        return jsonify(message="Error retrieving profile picture."), 500
    


@app.route('/open_homepage',methods=['GET','POST'])  
def open_homepage():
    profile_email = session.get('profile_email')
    userdata= get_user_desc(profile_email)
    return render_template("s-home page.html",userdata=userdata)

def get_or_create_chat(user_sender_id, user_receiver_id):
    mycursor.execute("""
        SELECT chat_id 
        FROM chats 
        WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s)
    """, (user_sender_id, user_receiver_id, user_receiver_id, user_sender_id))
    chat = mycursor.fetchone()
    
    if chat is None:
        mycursor.execute("""
            INSERT INTO chats (user1_id, user2_id, created_at) 
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        """, (user_sender_id, user_receiver_id))
        mydb.commit()
        chat_id = mycursor.lastrowid
    else:
        chat_id = chat[0]
    
    return chat_id

  

def load_chat(chat_id, user_sender_id):
    try:
        
        retrieve = """
        SELECT m.message_text, m.timestamp, m.status, u.username AS sender_username
        FROM messages m 
        JOIN user_details u ON m.sender_id = u.user_id
        WHERE m.chat_id = %s
        ORDER BY m.timestamp DESC
        """
        mycursor.execute(retrieve, (chat_id,))
        retrieved_messages = mycursor.fetchall()

        # Update message status to 'read' for messages received by the user
        status_update = """
        UPDATE messages
        SET status = 'read'
        WHERE chat_id = %s AND receiver_id = %s AND status = 'unread'
        """
        mycursor.execute(status_update, (chat_id, user_sender_id))
        mydb.commit()

        # Format retrieved messages into a list of dictionaries
        formatted_messages = []
        for msg in retrieved_messages:
            content_item = {
                'message_text': msg[0],
                'timestamp': msg[1],
                'status': msg[2],
                'sender_username': msg[3]
            }
            formatted_messages.append(content_item)
        
        return formatted_messages

    except Exception as e:
        logging.error(f"Error loading chat: {e}")
        return []



    

@app.route('/load_chat', methods=['GET'])
def get_load_chat():
    try:
        user_email = session.get('profile_email')
        sender_id = get_userid_from_email(user_email)
        if sender_id is not None:
            chats = get_all_chats(sender_id)
            groups = get_groups(sender_id)
            #combined_chats = chats + groups if chats and groups else chats or groups or []
            combined_chats=chats,groups
        else:
            combined_chats = []
       
        return jsonify(chats)
        #return render_template("chat.html", chats=chats, groups=groups, onchat="")

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/open_chat', methods=['GET', 'POST'])  
def open_chats():
    try:
        user_email = session.get('profile_email')
        sender_id = get_userid_from_email(user_email)
        if sender_id is not None:
            sender_id=str(sender_id)
            found_users = fetch_users()
            userdata = get_user_desc(user_email)
            chats = get_all_chats(sender_id)
            groups = get_groups(sender_id)
            success_msg="welcome to chats"
          
        else:
            None    
    except Exception as e:
        return jsonify({"error": str(e)}), 500        
    
    return render_template("s-chat.html", userdata=userdata,chats=chats, groups=groups,success_msg="helooo", found_users=found_users, onchat="")

def fetch_users():
    try:
        sql = "SELECT username, email, birthdate, gender, country, user_id, profile_pic FROM user_details"
        mycursor.execute(sql)
        userinfo = mycursor.fetchall()
     
        users_data = []
        for user_info in userinfo:
            user_data = {
                "Username": user_info[0],
                "Email": user_info[1],
                "Birthdate": user_info[2],
                "Gender": user_info[3],
                "Country": user_info[4],
                "user_id": user_info[5],
                "profile": user_info[6]
            }
            # Encode profile picture
            user_data['profile'] = encode_image(user_data['profile'])
            users_data.append(user_data)
        
        return users_data
    
    except Exception as e:
        error_msg=(f"An error occurred: {e}")
        return error_msg

def encode_image(file_path):
    try:      
        image_path = file_path

        with open(image_path, "rb") as image_file:
            # Encode the image to Base64
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # Create the full Base64 string with the data URL scheme
        message_file = f"data:image/jpeg;base64,{encoded_string}"
        return message_file

    except Exception as e:
        print("Error encoding image:", e)
        return None

@app.route('/create_group_chat_details', methods=['GET', 'POST'])
def create_group_chat_details():
    if request.method == 'POST':
        selected_users = request.form.getlist('selected_users')
        group_name = request.form.get('group_name')
        group_description = request.form.get('group_description')
        
        if 'group_profile_pic' in request.files:
            file = request.files['group_profile_pic']
        else:
            file = None

        create_group = insert_new_group(selected_users, group_name, file, group_description)

        if isinstance(create_group, str):
            
            return redirect(url_for('open_chats', success_msg=create_group))
        else:
          
            error_msg, = create_group
            return render_template('create_group.html', error_msg=error_msg)

    return render_template('create_group.html')


  

def insert_new_group(selected_users, group_name, file, description):
    your_email = session.get('profile_email')
    creator_id = get_userid_from_email(your_email)
    
    try:
        # Handle file upload
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            group_profile_pic = file_path
        else:
            group_profile_pic = "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\images\\groupicon.jpeg"

        
        insert_group_query = '''
        INSERT INTO group_chat (group_name, created_by, profile_pic, description)
        VALUES (%s, %s, %s, %s)
        '''
        mycursor.execute(insert_group_query, (group_name, creator_id, group_profile_pic, description))
        group_id = mycursor.lastrowid
        
        insert_creator_query = '''
        INSERT INTO group_members (group_id, user_id, role)
        VALUES (%s, %s, %s)
        '''
        mycursor.execute(insert_creator_query, (group_id, creator_id, 'admin'))
        
        insert_members_query = '''
        INSERT INTO group_members (group_id, user_id, role)
        VALUES (%s, %s, %s)
        '''
        for user_id in selected_users:
           
            check_member_query = '''
            SELECT COUNT(*) FROM group_members WHERE group_id = %s AND user_id = %s
            '''
            mycursor.execute(check_member_query, (group_id, user_id))
            count = mycursor.fetchone()[0]
            
            if count == 0:
                mycursor.execute(insert_members_query, (group_id, user_id, 'member'))
        
        mydb.commit()
        success_msg = "Group created successfully"
       
        return success_msg

    except Exception as err:
        mydb.rollback() 
        error_msg=str(err)
        return error_msg

 
@app.route('/create_group_chat', methods=['GET', 'POST'])
def send_chat():
    user_email = session.get('profile_email')
    msg = "Choose users to create a Group"
    try:
        sender_id = get_userid_from_email(user_email)

        if sender_id is not None:
            chats = get_all_chats(sender_id)

            mycursor.execute("SELECT group_name FROM group_chat")
            groupnames = mycursor.fetchall()
            
            groups = [group[0] for group in groupnames if group]
            
            return render_template('create_group.html', chats=chats, groupnames=groups,help_msg=msg)
        else:
            error_msg = "Error with your user ID, try again later!"
            return render_template('s-chat.html', error_msg=error_msg)
    
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        return render_template('s-chat.html', error_msg=error_msg)

   

    
#.....................................................................................................................
import mysql.connector
from flask import Flask, request, jsonify, render_template, session
from flask_socketio import SocketIO
from datetime import datetime
import logging
import uuid
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import json



socketio = SocketIO(app)
logging.basicConfig(level=logging.DEBUG)

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='0000',
    database='details'
)
cursor = conn.cursor()

class Chat:
    @staticmethod
    def generate_room_id(user1, user2):
        cursor.execute('''
            SELECT chat_id FROM chats
            WHERE (user1 = %s AND user2 = %s) OR (user1 = %s AND user2 = %s)
        ''', (user1, user2, user2, user1))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            chat_id = str(uuid.uuid4())  # Generate a unique alphanumeric ID
            cursor.execute('''
                INSERT INTO chats (chat_id, user1, user2, updated_at)
                VALUES (%s, %s, %s, %s)
            ''', (chat_id, user1, user2, datetime.now()))
            conn.commit()
            return chat_id
        

@app.route('/get_chat_id', methods=['GET', 'POST'])
def get_chat_id():
    profile_email = session.get('profile_email')
    if profile_email is None:
        return "<p style='color:red;'>Invalid sender email</p>", 400
    
    user_receiver_id = request.form.get('user_receiver_id')
    print(user_receiver_id)
    if not user_receiver_id:
        return "<p style='color:red;'>Invalid receiver ID</p>", 400
    
    try:
        user_receiver_id = int(user_receiver_id)
       
    except ValueError:
        return "<p style='color:red;'>Invalid receiver ID format</p>", 400
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0000',
            database='details'
        )
        cursor = conn.cursor()
    except Error as e:
        return f"Error connecting to database: {e}", 500

    try: 
        user_sender_id = get_userid_from_email(profile_email)
        
        if user_sender_id is None:
            return "<p style='color:red;'>Invalid sender email</p>", 400
        
       
    
        cursor.execute("SELECT email FROM user_details WHERE user_id = %s", (user_receiver_id,))
        receiver_email = cursor.fetchone()
        if receiver_email is None:
            return "<p style='color:red;'>Invalid receiver ID</p>", 400
        receiver_email = receiver_email[0]
    
        current_user_id = str(user_sender_id)
        user_receiver_id = user_receiver_id
        chat_id = Chat.generate_room_id(current_user_id, user_receiver_id)
        
        messages = get_messages(chat_id)
        found_users=fetch_users()
        onchat=get_profilepic_username(user_receiver_id,)
        userdata= get_user_desc(profile_email)
        
        
        try:
            user_email = session.get('profile_email')
            sender_id = get_userid_from_email(user_email)
            if sender_id is not None:
                chats = get_all_chats(sender_id)
            else:
                chats = []
        
            #return jsonify(chats)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    except Error as e:
        return f"Error connecting to database: {e}", 500
    
    
    return render_template('chat.html', messages=messages,chats=chats, onchat=onchat,profile_email=user_sender_id, current_user_id=current_user_id,receivers_email=user_receiver_id,chat_code=chat_id,receiver_email=receiver_email,found_users=found_users,userdata=userdata)

        
def get_profilepic_username(user_id):
    mycursor.execute("SELECT profile_pic, username,bio ,phone,address,email,intrest FROM user_details WHERE user_id = %s", (user_id,))
    info = mycursor.fetchall()
    pic_username = []

    for uinfo in info:
        onchatinfo = {
            "pic": uinfo[0],
            "username": uinfo[1],
            "bio":uinfo[2],
            "phone":uinfo[3],
            "address":uinfo[4],
            "email":uinfo[5],
            "interest":uinfo[6]
        }
        if onchatinfo['pic'] is not None:
            onchatinfo['pic'] = encode_image(onchatinfo['pic'])
    
        else:
          image=  "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\images\\bald placeholder.jpg"
          onchatinfo['pic'] = encode_image(image)
        pic_username.append(onchatinfo)
    
    return pic_username


from datetime import datetime

def format_date(date_obj):
    try:
        formatted_date = date_obj.strftime("%a %d %b %Y %I:%M %p")
        return formatted_date
    except Exception as e:
        print(f"Error: {e}")
        return str(date_obj)
    
def get_all_chats(sender_id):
    try:
        sql = """
        SELECT MAX(message_id), receiver_id, MAX(message_text), MAX(timestamp) 
        FROM messages 
        WHERE sender_id = %s OR receiver_id = %s 
        GROUP BY receiver_id 
        ORDER BY MAX(timestamp) DESC
        """
        mycursor.execute(sql, (sender_id, sender_id))
        activechats = mycursor.fetchall()

        chats = []
        if activechats:
            for datain in activechats:
                mycursor.execute("SELECT profile_pic, username FROM user_details WHERE user_id = %s", (datain[1],))
                pic_info = mycursor.fetchone()

                if pic_info:
                    profile_pic_path = pic_info[0]
                    receivername = pic_info[1]
                else:
                    profile_pic_path = "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\images\\bald placeholder.jpg"
                    receivername = "Unknown"

                sender_pic = encode_image(profile_pic_path)
                formatted_date = format_date(datain[3]) if datain[3] is not None else "Unknown time"

                new_chats = {
                    "message_id": datain[0],
                    "receiver_id": datain[1],
                    "messages": datain[2],
                    "time": formatted_date,
                    "receiver_name": receivername,
                    "profile_pic": sender_pic,
                    "type": "individual" 
                }
                chats.append(new_chats)
            return chats
        else:
            return []
    except Exception as err:
        print(f"Error in get_all_chats: {err}")
        return []


def get_groups(sender_id):
    try:
        sql_group_ids = """
        SELECT group_id
        FROM group_members
        WHERE user_id = %s
        """
        mycursor.execute(sql_group_ids, (sender_id,))
        group_ids = mycursor.fetchall()
        
        print(group_ids)
        
        if not group_ids:
            return ":no groups found"

        # Convert fetched group IDs to a tuple
        group_ids_tuple = tuple(group_id[0] for group_id in group_ids)
        print(group_ids_tuple)

        placeholders = ', '.join(['%s'] * len(group_ids_tuple))
        print(placeholders)
        
        sql_group_chats = f"""
        SELECT gc.group_id, gc.group_name, gc.profile_pic, MAX(gm.content), MAX(gm.timestamp)
        FROM group_chat gc
        LEFT JOIN group_messages gm ON gc.group_id = gm.group_id
        WHERE gc.group_id IN ({placeholders})
        GROUP BY gc.group_id, gc.group_name, gc.profile_pic
        ORDER BY MAX(gm.timestamp) DESC
        """
        mycursor.execute(sql_group_chats, group_ids_tuple)
        group_in = mycursor.fetchall()
        print(group_in)

        groups = []
        if group_in:
            for group in group_in:
                profile_pic_path = group[2] if group[2] else "C:\\Users\\NICHOLAS\\OneDrive\\Desktop\\myproject4\\static\\images\\groupicon.jpeg"
                group_pic = encode_image(profile_pic_path)
                formatted_date = format_date(group[4]) if group[4] is not None else "Unknown time"

                new_group_chats = {
                    "group_id": group[0],
                    "group_name": group[1],
                    "profile_pic": group_pic,
                    "messages": group[3] if group[3] is not None else "No messages",
                    "time": formatted_date,
                    "type": "group"
                }
                groups.append(new_group_chats)
            return groups
        else:
            return ":no groups found"
    except Exception as err:
        print(f"Error: {err}")
        return []
    


def get_messages(chat_id):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="0000",
            database="details"
        )
        
        mycursor = mydb.cursor()

        select_messages_query = '''
                SELECT m.message_id, m.sender_id, m.receiver_id, m.message_text, m.timestamp, m.status,images
                FROM messages m
                WHERE m.chat_id = %s
                ORDER BY m.timestamp DESC
            '''  

        mycursor.execute(select_messages_query, (chat_id,))
        messages = mycursor.fetchall()
    
        chats = []
        for new in messages:
            new_chats = {
                "message": new[1],
                "chat": new[3],
                "time": format_date(new[4]),
                "status": new[5],
                "images": new[6],
            
            }
            # Encode images
            if  new_chats['images'] is  not None:
             new_chats['images'] = encode_image(new_chats['images'])
            chats.append(new_chats)
        return chats
    except Exception as err:
        return err

def get_userid_from_email(your_email):
    try:
        cursor.execute("SELECT user_id FROM user_details WHERE email = %s", (your_email,))
        user_sender_id = cursor.fetchone()
        user_sender_id=user_sender_id[0]
    except Exception as err:
        return err
    
    return user_sender_id
        
    

def get_username_from_id(user_id):
    cursor.execute("SELECT email FROM user_details WHERE user_id = %s", (user_id,))
    receiver_email = cursor.fetchone()
    if receiver_email is None:
       return user_id
    useremail = receiver_email[0]
    return useremail

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

users = {}

def get_db_connection():
    conn = sqlite3.connect('details')
    conn.row_factory = sqlite3.Row
    return conn


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    users[username] = room
    user_name=get_username_from_id(username)
    send(f"{username} has entered the room.", to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    users.pop(username, None)
    user_name=get_username_from_id(username)
    send(f"{user_name} has left the room.", to=room)
    
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(success=False, message='No file part')
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message='No selected file')
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify(success=True, filePath=file_path)
    
    return jsonify(success=False, message='File upload failed')
    
    
from datetime import datetime
from flask_socketio import SocketIO, emit

@socketio.on('private_message')
def handle_private_message(data):
    recipient_username = data['recipient']
    sender_username = data['sender']
    message_text = data['message']
    message_file=data['file']
    
   
           
    chat_id = Chat.generate_room_id(sender_username, recipient_username)
    logging.info(f"Generated chat room ID: {chat_id}")

    insert_message_query = '''
        INSERT INTO messages (sender_id, receiver_id, chat_id, message_text,images)
        VALUES (%s, %s, %s, %s,%s)
    '''
    cursor.execute(insert_message_query, (sender_username, recipient_username, chat_id, message_text,message_file))
    message_id = cursor.lastrowid
    
    update_chat_query = '''
        UPDATE chats
        SET last_message_id = %s, updated_at = %s
        WHERE chat_id = %s
    '''
    cursor.execute(update_chat_query, (message_id, datetime.now(), chat_id))
    if cursor.rowcount == 0:
        insert_chat_query = '''
            INSERT INTO chats (chat_id, user1_id, user2_id, last_message_id, updated_at)
            VALUES (%s, %s, %s, %s, %s)
        '''
        cursor.execute(insert_chat_query, (chat_id, sender_username, recipient_username, message_id, datetime.now()))
        
    conn.commit()
    message_file = message_file if message_file else None
    message_file=encode_image(message_file)
    new_message = {
        'sender_id': sender_username,
        'receiver_id': recipient_username,
        'chat_id': chat_id,
        'message_text': message_text,
        'message_file': message_file,
       
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Emit the new message to the recipient
    recipient_room = users.get(recipient_username)
    if recipient_room:
      emit('new_message', new_message, room=recipient_room)  # Emit to recipient's room if available
    else:  
     emit('new_message', new_message, room=request.sid)  # Emit to sender's room

   
   

   
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    users[username] = request.sid
    emit('message', {'msg': f'{username} has entered the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    users.pop(username, None)
    emit('message', {'msg': f'{username} has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    sender = data['sender']
    recipient = data.get('recipient')

    if recipient:
        # Send the private message to the recipient's session ID
        recipient_sid = users.get(recipient)
        if recipient_sid:
            emit('message', {'msg': f'Private to {recipient} from {sender}: {msg}', 'sender': sender}, room=recipient_sid)
        # Broadcast the private message to the entire room, indicating it is private
        emit('message', {'msg': f'{sender} (to {recipient}): {msg}'}, room=room)
    else:
        # Broadcast message to the entire room
        emit('message', {'msg': f'{sender}: {msg}'}, room=room)
     
     
@app.route('/join_group_chat', methods=['GET', 'POST'])
def join_group_chat():
    profile_email = session.get('profile_email')
    group_room=request.form.get("group_room")
    user_receiver_id = request.form.get('user_receiver_id')
    
    print("group room:",group_room)
    return render_template('chat.html',profile_email=profile_email,group_room=group_room)
       
        

if __name__ == '__main__':
    socketio.run(app, debug=True)
