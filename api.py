from flask import Flask, jsonify, request
from mysql.connector import connect, Error
from contextlib import closing
from werkzeug.utils import secure_filename
import blursbs_config as config
import base64
import os
import requests
import json
UPLOAD_FOLDER = '/data/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'png', 'jpg', 'jpeg'}
 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_connection():
    return connect(
        host=config.host,
        user=config.user,
        password=config.password,
        database=config.database,
    )

def get_media_result(connection, media_id,media_email):
    with closing(connection.cursor(buffered=True)) as cursor:
        cursor.execute("SELECT `id`,`email`,`filename`,`filesize`,`fileext`,`status`,`upload_date`, `expiration_date`,`download_path`,`webhook` FROM `media` WHERE `id` = %s AND `email` = %s;", (media_id, media_email))
        result = cursor.fetchmany(size=1)
        response = None
        for row in result:
            response = {}
            response["media_id"] = base64.urlsafe_b64encode(row[1]+"|"+row[0])
            response["email"] = row[1]
            response["file_name"] = row[2]
            response["file_size"] = row[3]
            response["file_ext"] = row[4]
            response["status"]   = row[5]
            response["upload_date"] = row[6]
            response["expiration_date"] = row[7]
            response["download_path"] = row[8]
            response["webhook"] = row[9]
        if response==None:
            response = {"error_code": 404, "error": "Record not found"}
        return jsonify(response)

def call_webhook(URL, DATA):
    headers = {'User-Agent': 'Blur-SBS API/1.0'}
    session = requests.Session()
    return json.loads(session.post(URL,headers=headers,data=DATA).text)

@app.route("/api/v1/media", methods=["POST"])
def media_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error_type": 400, "error":"No file in request"})
        file = request.files['file']
        media_email = request.form.get("email")
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({"error_type": 400, "error":"No file in request"})
        if media_email == '' or ("@" not in media_email and "." not in media_email):
            return jsonify({"error_type": 400, "error":"Invalid Email Address"})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Tell blur.sbs that we have uploaded a new file.
            data =  {
                        "form":
                            {
                                "name": "BlurSBSUpload"
                            }, 
                        "fields":
                            {
                                "email":
                                    {
                                        "raw_value": media_email
                                    },
                                "file":
                                    {
                                        "raw_value": filename
                                    }
                            }
                    }
            response = call_webhook(config.webhook_url, data)
            with closing(get_connection) as connection:
                return get_media_result(connection, response["id"], response["email"])
        else:
            return jsonify({"error_type":400,"error":"File type not allowed"})

@app.route("/api/v1/media/<id>", methods=["GET"])
def media_get(id):
    if request.method=='GET':
        try:
            with closing(get_connection()) as connection:
                id = base64.urlsafe_b64decode(id+"===").split("|")
                media_id = int(id[1])
                media_email = id[0]
                return get_media_result(connection, media_id, media_email)
        except Error as e:
            print("Error in main connection thread: " + str(e))
            response = {"error_code": 500, "error": "Error retrieving results"}
            return jsonify(response)


#  main thread of execution to start the server
if __name__=='__main__':
   app.run(debug=config.debug)