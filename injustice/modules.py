from flask import Flask, jsonify, request,render_template
import os
import base64

app = Flask(__name__)

# Sample data to simulate fetching from a database
data = [
    {"id": 1, "title": "Data 1", "date": "2024-05-21", "content": "Content 1"},
    {"id": 2, "title": "Data 2", "date": "2024-05-20", "content": "Content 2"},
    {"id": 3, "title": "Data 3", "date": "2024-05-19", "content": "Content 3"},
    # Add more sample data here
]

# Mock function to fetch data from the database
def fetch_data_from_db(page, limit):
    start_index = (page - 1) * limit
    end_index = start_index + limit
    return data[start_index:end_index]

# Mock function to fetch media files from the database
def fetch_media_files(content_id):
    # Replace with actual database logic
    return [
        {"file_path": "/path/to/image1.jpg"},
        {"file_path": "/path/to/video1.mp4"},
        # Add more media files
    ]

@app.route('/')
def data():
    return render_template('index.html')

@app.route('/fetch-data')
def fetch_data():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    content_data = fetch_data_from_db(page, limit)
    
    for content in content_data:
        content_id = content['id']
        media_files = fetch_media_files(content_id)
        
        content['media'] = []
        for media_file in media_files:
            file_path = media_file['file_path']
            file_extension = os.path.splitext(file_path)[-1].lower()
            
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                with open(file_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                content['media'].append({
                    "type": "image",
                    "src": f"data:image/{file_extension[1:]};base64,{encoded_image}"
                })
            elif file_extension in ['.mp4', '.avi', '.mov', '.wmv']:
                content['media'].append({
                    "type": "video",
                    "src": file_path
                })
    
    return jsonify(content_data)

@app.route('/fetch-video')
def fetch_video():
    file_path = request.args.get('file_path')
    
    if not file_path:
        return jsonify({"error": "File path is required"}), 400
    
    try:
        with open(file_path, "rb") as video_file:
            encoded_video = base64.b64encode(video_file.read()).decode("utf-8")
        return jsonify({"src": f"data:video/mp4;base64,{encoded_video}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time

def send_email():
    # Set up email content
    from_email = 'your_email@gmail.com'
    to_email = 'recipient_email@example.com'
    subject = 'Daily Report'
    body = 'This is your daily report.'

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Create the body of the message (a plain-text and an HTML version).
    text = body
    html = """\
    <html>
      <body>
        <p>{}</p>
      </body>
    </html>
    """.format(body)

    # Attach both plain-text and HTML versions
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    # Send the message via SMTP server.
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'your_email@gmail.com'
    smtp_password = 'your_email_password'

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

# Schedule the task to run daily at a specific time (e.g., 9:00 AM)
schedule.every().day.at("09:00").do(send_email)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute
