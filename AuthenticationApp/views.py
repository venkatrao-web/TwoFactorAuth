from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
from datetime import date
import cv2
import numpy as np
import base64
import random
from datetime import datetime
from PIL import Image
import face_recognition
import pymysql
import random
import smtplib

global username, password, contact, email, address, thumb, aadhar, names, encodings, thumb_data
global usersList, partyList, voteList, otp

def getUsersList():
    global usersList
    usersList = []
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'votingapp',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select * from register")
        rows = cur.fetchall()
        for row in rows:
            usersList.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6]])

def getPartyList():
    global partyList
    partyList = []
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'votingapp',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select * from addparty")
        rows = cur.fetchall()
        for row in rows:
            partyList.append([row[0], row[1], row[2], row[3]])

def getVoteList():
    global voteList
    voteList = []
    con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'votingapp',charset='utf8')
    with con:
        cur = con.cursor()
        cur.execute("select * from votes")
        rows = cur.fetchall()
        for row in rows:
            voteList.append([row[0], row[1], row[2], row[3]])

def loadModel():
    global names, encodings
    if os.path.exists("model/encoding.npy"):
        encodings = np.load("model/encoding.npy")
        names = np.load("model/names.npy")        
    else:
        encodings = []
        names = []   
    
getUsersList()
getPartyList()        
getVoteList()
loadModel()

face_detection = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def alreadyCastVote(candidate):
    global voteList
    count = 0
    for i in range(len(voteList)):
        vl = voteList[i]
        if vl[0] == candidate:
            count = 1
    return count

def FinishVote(request):
    if request.method == 'GET':
        global username, voteList
        cname = request.GET.get('cname', False)
        pname = request.GET.get('pname', False)
        voter = ''
        today = date.today()
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'votingapp',charset='utf8')
        db_cursor = db_connection.cursor()
        student_sql_query = "INSERT INTO votes(username, candidatename, partyname, vote_date) VALUES('"+username+"','"+cname+"','"+pname+"','"+str(today)+"')"
        db_cursor.execute(student_sql_query)
        db_connection.commit()
        voteList.append([username, cname, pname, str(today)])
        context= {'data':'<font size=3 color=black>Your Vote Accepted for Candidate '+cname}
        return render(request, 'UserScreen.html', context)

def getOutput(status):
    global partyList
    output = '<h3><br/>'+status+'<br/><table border=1 align=center>'
    output+='<tr><th><font size=3 color=black>Candidate Name</font></th>'
    output+='<th><font size=3 color=black>Party Name</font></th>'
    output+='<th><font size=3 color=black>Area Name</font></th>'
    output+='<th><font size=3 color=black>Image</font></th>'
    output+='<th><font size=3 color=black>Cast Vote Here</font></th></tr>'
    for i in range(len(partyList)):
        pl = partyList[i]
        output+='<tr><td><font size=3 color=black>'+pl[0]+'</font></td>'
        output+='<td><font size=3 color=black>'+pl[1]+'</font></td>'
        output+='<td><font size=3 color=black>'+pl[2]+'</font></td>'
        output+='<td><img src="/static/parties/'+pl[3]+'" width=200 height=200></img></td>'
        output+='<td><a href="FinishVote?cname='+pl[0]+'&pname='+pl[1]+'"><font size=3 color=black>Click Here</font></a></td></tr>'
    output+="</table><br/><br/><br/><br/><br/><br/>"        
    return output   

def ValidateUser(request):
    if request.method == 'POST':
        global username, encodings, names
        predict = "none"
        page = "UserScreen.html"
        status = "unable to predict user"
        img = cv2.imread('AuthenticationApp/static/photo/test.png')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_component = None
        faces = face_detection.detectMultiScale(img,scaleFactor=1.1,minNeighbors=5,minSize=(30,30),flags=cv2.CASCADE_SCALE_IMAGE)
        status = "Unable to predict.Please retry"
        faces = sorted(faces, reverse=True,key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
        (fX, fY, fW, fH) = faces
        face_component = gray[fY:fY + fH, fX:fX + fW]
        if face_component is not None:
            img = cv2.resize(img, (600, 600))
            rgb_small_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert the frame to RGB color space
            face_locations = face_recognition.face_locations(rgb_small_frame)  # Locate faces in the frame
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)  # Encode faces in the frame
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(encodings, face_encoding)  # Compare face encodings
                face_distance = face_recognition.face_distance(encodings, face_encoding)  # Calculate face distance
                best_match_index = np.argmin(face_distance)  # Get the index of the best match
                print(best_match_index)
                if matches[best_match_index]:  # If the face is a match
                    name = names[best_match_index]  # Get the corresponding name
                    predict = name
                    break
        if predict == username:
            count = alreadyCastVote(username)
            if count == 0:
                page = 'VotePage.html'
                status = getOutput("User predicted as : "+predict+"<br/><br/>")
            else:
                status = "You already casted your vote"
                page = "UserScreen.html"
        else:
            page = "UserScreen.html"
            status = "unable to predict user"
        context= {'data':status}
        return render(request, page, context)

def sendOTP(email, otp_value):
    em = []
    em.append(email)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        email_address = 'kaleem202120@gmail.com'
        email_password = 'xyljzncebdxcubjq'
        connection.login(email_address, email_password)
        connection.sendmail(from_addr="kaleem202120@gmail.com", to_addrs=em, msg="Subject : Your OTP : "+otp_value)

def OTPValidation(request):
    if request.method == 'POST':
        global otp
        otp_value = request.POST.get('t1', False)
        if otp == otp_value:
            context= {'data':"OTP Validation Successful"}
            return render(request, "UserScreen.html", context)
        else:
            context= {'data':"Invalid OTP! Please retry"}
            return render(request, "OTP.html", context)            

def UserLogin(request):
    if request.method == 'POST':
        global username, usersList, aadhar, otp
        username = request.POST.get('username', False)
        aadhar = request.POST.get('password', False)
        thumb_data = request.FILES['thumb'].read()
        status = "Login.html"
        output = 'Invalid login details'
        for i in range(len(usersList)):
            ulist = usersList[i]
            user1 = ulist[0]
            pass1 = ulist[1]
            thumb = ulist[5]
            aadhar1 = ulist[6]
            email = ulist[3]
            with open("AuthenticationApp/static/thumb/"+thumb, "rb") as file:
                data = file.read()
            file.close()
            if user1 == username and aadhar1 == aadhar and data == thumb_data:
                otp = str(random.randint(1000, 9999))
                sendOTP(email, otp)
                status = "OTP.html"
                output = 'Welcome '+username
                break        
        context= {'data':output}
        return render(request, status, context)

def AdminLogin(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        if username == 'admin' and password == 'admin':
            context= {'data':'Welcome '+username}
            return render(request, 'AdminScreen.html', context)
        if status == 'none':
            context= {'data':'Invalid login details'}
            return render(request, 'Admin.html', context)

def AddParty(request):
    if request.method == 'GET':
       return render(request, 'AddParty.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def CastVote(request):
    if request.method == 'GET':
       return render(request, 'CastVote.html', {})    

def AddVoter(request):
    if request.method == 'GET':
       return render(request, 'AddVoter.html', {})

def Admin(request):
    if request.method == 'GET':
       return render(request, 'Admin.html', {})

def AddVoterAction(request):
    if request.method == 'POST':
      global username, password, contact, email, address, usersList, thumb, aadhar, thumb_data
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      contact = request.POST.get('contact', False)
      email = request.POST.get('email', False)
      address = request.POST.get('address', False)
      aadhar = request.POST.get('aadhar', False)
      thumb_data = request.FILES['thumb'].read()
      thumb = request.FILES['thumb'].name
      status = "none"
      for i in range(len(usersList)):
          ul = usersList[i]
          if username == ul[0]:
              status = "exists"
              break
      if status == "none":
          context= {'data':'Capture Your face'}
          return render(request, 'CaptureFace.html', context)
      else:
          context= {'data':username+' Username already exists'}
          return render(request, 'AddVoter.html', context)

def WebCam(request):
    if request.method == 'GET':
        data = str(request)
        formats, imgstr = data.split(';base64,')
        imgstr = imgstr[0:(len(imgstr)-2)]
        data = base64.b64decode(imgstr)
        if os.path.exists("AuthenticationApp/static/photo/test.png"):
            os.remove("AuthenticationApp/static/photo/test.png")
        with open('AuthenticationApp/static/photo/test.png', 'wb') as f:
            f.write(data)
        f.close()
        context= {'data':"done"}
        return HttpResponse("Image saved")        
    
def saveFace():
    global names, encodings
    encodings = np.asarray(encodings)
    names = np.asarray(names)
    np.save("model/encoding", encodings)
    np.save("model/names", names)

def saveUser(request):
    if request.method == 'POST':
        global username, password, contact, email, address, usersList, encodings, names, thumb, aadhar, thumb_data
        img = cv2.imread('AuthenticationApp/static/photo/test.png')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_component = None
        faces = face_detection.detectMultiScale(gray, 1.3,5)
        page = "AddVoter.html"
        status = 'Unable to detect face. Please retry'
        for (x, y, w, h) in faces:
            face_component = img[y:y+h, x:x+w]
        if face_component is not None:
            img = cv2.resize(img, (600, 600))
            if os.path.exists("AuthenticationApp/static/photo/test.png"):
                os.remove("AuthenticationApp/static/photo/test.png")
            cv2.imwrite("AuthenticationApp/static/photo/test.png", img)
            image = face_recognition.load_image_file("AuthenticationApp/static/photo/test.png")
            encoding = face_recognition.face_encodings(image)
            print("encoding "+str(encoding))
            if len(encoding) > 0 and username not in names:
                encoding = encoding[0]
                if len(encodings) == 0:
                    encodings.append(encoding)
                    names.append(username)
                else:
                    encodings = encodings.tolist()
                    names = names.tolist()
                    encodings.append(encoding)
                    names.append(username)
                saveFace()
                page = "AddVoter.html"
                status = 'User with Face, thumb and aadhar Details added to Database<br/><br/>'
                db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'votingapp',charset='utf8')
                db_cursor = db_connection.cursor()
                student_sql_query = "INSERT INTO register(username,password,contact,email,address,thumb,aadhar) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"','"+thumb+"','"+aadhar+"')"
                db_cursor.execute(student_sql_query)
                db_connection.commit()
                if os.path.exists("AuthenticationApp/static/thumb/"+thumb):
                    os.remove("AuthenticationApp/static/thumb/"+thumb)
                with open("AuthenticationApp/static/thumb/"+thumb, "wb") as file:
                    file.write(thumb_data)
                file.close()    
                usersList.append([username, password, contact, email, address, thumb, aadhar])
        context= {'data': status}
        return render(request, page, context)

def AddPartyAction(request):
    if request.method == 'POST':
        global partyList
        cname = request.POST.get('t1', False)
        pname = request.POST.get('t2', False)
        area = request.POST.get('t3', False)
        myfile = request.FILES['t4']
        imagename = request.FILES['t4'].name
        status = "none"
        page = "AddParty.html"
        for i in range(len(partyList)):
            pl = partyList[i]
            if cname == pl[0] and pname == pl[1]:
                status = "Candidate & Party Name Already Exists"
                break
        if status == "none":
            fs = FileSystemStorage()
            filename = fs.save('AuthenticationApp/static/parties/'+imagename, myfile)
            status = 'Candidate details added'
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'votingapp',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO addparty() VALUES('"+cname+"','"+pname+"','"+area+"','"+imagename+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            partyList.append([cname, pname, area, imagename])
        context= {'data': status}
        return render(request, page, context)


def getVoteCount(cname, pname):
    global voteList
    count = 0
    for i in range(len(voteList)):
        vl = voteList[i]
        if vl[1] == cname and vl[2] == pname:
            count += 1
    return count        

def ViewVotes(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Candidate Name</font></th>'
        output+='<th><font size=3 color=black>Party Name</font></th>'
        output+='<th><font size=3 color=black>Area Name</font></th>'
        output+='<th><font size=3 color=black>Image</font></th>'
        output+='<th><font size=3 color=black>Vote Count</font></th>'
        for i in range(len(partyList)):
            pl = partyList[i]
            count = getVoteCount(pl[0], pl[1])
            output+='<tr><td><font size=3 color=black>'+pl[0]+'</font></td>'
            output+='<td><font size=3 color=black>'+pl[1]+'</font></td>'
            output+='<td><font size=3 color=black>'+pl[2]+'</font></td>'
            output+='<td><img src="/static/parties/'+pl[3]+'" width=200 height=200></img></td>'
            output+='<td><font size=3 color=black>'+str(count)+'</font></td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"        
        context= {'data':output}
        return render(request, 'ViewVotes.html', context)    
            
def ViewParty(request):
    if request.method == 'GET':
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Candidate Name</font></th>'
        output+='<th><font size=3 color=black>Party Name</font></th>'
        output+='<th><font size=3 color=black>Area Name</font></th>'
        output+='<th><font size=3 color=black>Image</font></th></tr>'
        for i in range(len(partyList)):
            pl = partyList[i]
            output+='<tr><td><font size=3 color=black>'+pl[0]+'</font></td>'
            output+='<td><font size=3 color=black>'+pl[1]+'</font></td>'
            output+='<td><font size=3 color=black>'+pl[2]+'</font></td>'
            output+='<td><img src="/static/parties/'+pl[3]+'" width=200 height=200></img></td></tr>'
        output+="</table><br/><br/><br/><br/><br/><br/>"        
        context= {'data':output}
        return render(request, 'ViewParty.html', context)    
      
