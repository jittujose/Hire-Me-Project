from datetime import datetime
import random
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token;
from google.auth.transport import requests
from google.cloud import firestore, storage
import starlette.status as status
import local_constants
import math
import pytz

app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

def getUser(user_token):
    user = firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data = {
            'email':user_token['email'],
            'name': '',
            'category':'',
            'field':'',
            'avail':'No'  
        }
        firestore_db.collection('users').document(user_token['user_id']).set(user_data)

    return user

def validateFirebaseToken(id_token):
    if not id_token:
        return None
    
    user_token = None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
    except ValueError as err:
        print(str(err))

    return user_token

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)
    print(user_token)
    if not user_token:
        return templates.TemplateResponse('main.html',{'request': request,'user_token':None,'error_message': None, 'user_info':None})
    
    user = getUser(user_token).get()

    if user.get('name') == 'admin':
        pendingUsers =[]
        usersref = firestore_db.collection('users').get()
        for oneuser in usersref:
            if oneuser.get('status')=='Pending':
                pendingUsers.append(oneuser)
        return templates.TemplateResponse('admin.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'pending_users':pendingUsers})
    
    if user.get('category') == '':
        return templates.TemplateResponse('registration.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user})
    
    if user.get('status') == 'Pending':
        return templates.TemplateResponse('pending.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user})
    elif user.get('status') == 'Rejected':
        return templates.TemplateResponse('rejected.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user})

    
    if user.get('category') == 'Employee' :
        hiringReqs =[]
        hiringReqs = firestore_db.collection('hirings').where('emplEmail', '==', user.get('email')).where('status', '==', 'Pending').get()
        jobs=[]
        jobs=firestore_db.collection('jobs').where('jobtype', '==', user.get('field')).where('status', '==', 'Pending').get()
        wins=firestore_db.collection('bidWins').where('jobtype', '==', user.get('field')).where('emplEmail', '==', user.get('email')).get()
        return templates.TemplateResponse('employeehome.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'hiringReqs': hiringReqs,'jobs':jobs,'wins':wins})
    # addresses = []
    # for address in user.get('address_list'):
    #     addresses.append(address.get())
    hiringReqs=[]
    hiringReqs = firestore_db.collection('hirings').get()
    oneHire = []
    for doc in hiringReqs:
        if doc.get('userEmail') == user.get("email") and doc.get('status') != "Completed":
            oneHire.append(doc)
            return templates.TemplateResponse('userHiringReq.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':oneHire})
    
    postedJobs = firestore_db.collection('jobs').where('userEmail','==',user.get('email')).get()
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'posted_jobs':postedJobs})


@app.post("/add-category", response_class=HTMLResponse)
async def addCategory(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    user = getUser(user_token).get()
    if form['options'] == 'User':
        st = "Approved"
    else:
        st = "Pending"
    user_data = {
                'email':user_token['email'],
                'name': form['name'],
                'category':form['options'],
                'field':'',
                'status':st,
                'filename':'',
                'avail':'No'
            }
    firestore_db.collection('users').document(user_token['user_id']).set(user_data)

    if form['options'] == 'User':
        return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse('emplReg.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user})

#For file uploading
def addFile(file):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    print(file)
    blob = storage.Blob(file.filename, bucket)
    blob.upload_from_file(file.file)
    return blob.public_url

def blobList(prefix):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)

    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET,prefix=prefix)

def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    blob = bucket.get_blob(filename)
    return blob.download_as_bytes()

@app.post("/emplreg", response_class=HTMLResponse)
async def emplReg(request: Request):

    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    user = getUser(user_token).get()
    src = ''
    src = addFile(form['document'])
    user_data = {
                'email':user_token['email'],
                'name': user.get('name'),
                'category':user.get('category'),
                'field':form['options'],
                'filename':src,
                'status':'Pending',
                'avail':'No',
                'hrCharge':form['hrCharge'],
                'walletAddress':form['walletAddress'],
                'rating':"",
                'ratingArr':[]
            }
    firestore_db.collection('users').document(user_token['user_id']).set(user_data)
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/approve_user", response_class=HTMLResponse)
async def approveUser(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    targetEmail=form['email']
    user_doc_ref = firestore_db.collection('users').where('email','==',targetEmail).get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        userID = doc.id
        oneUser['status']="Approved"
        firestore_db.collection('users').document(userID).set(oneUser)
    
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
    
@app.post("/reject_user", response_class=HTMLResponse)
async def approveUser(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    targetEmail=form['email']
    user_doc_ref = firestore_db.collection('users').where('email','==',targetEmail).get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        userID = doc.id
        oneUser['status']="Rejected"
        firestore_db.collection('users').document(userID).set(oneUser)
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/activate", response_class=HTMLResponse)
async def activateEmpl(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    targetEmail=form['email']
    userlocation = form['location']
    user_doc_ref = firestore_db.collection('users').where('email','==',targetEmail).get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        userID = doc.id
        oneUser['avail']="Active"
        oneUser['location']= userlocation
        firestore_db.collection('users').document(userID).set(oneUser)
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/deactivate", response_class=HTMLResponse)
async def activateEmpl(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    targetEmail=form['email']
    
    user_doc_ref = firestore_db.collection('users').where('email','==',targetEmail).get()
    for doc in user_doc_ref:
        oneUser = doc.to_dict()
        userID = doc.id
        oneUser['avail']="No"
        oneUser['location']= ""
        firestore_db.collection('users').document(userID).set(oneUser)
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)


#sorting object array based on user location
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def sort_objects_by_distance(reference_location, objects):
    ref_lat, ref_lon = map(float, reference_location.split(','))
    
    def distance_to_ref(obj):
        loc = obj.get('location')
        lat, lon = map(float, loc.split(','))
        return haversine_distance(ref_lat, ref_lon, lat, lon)
    
    return sorted(objects, key=distance_to_ref)

@app.post("/serachEmpl", response_class=HTMLResponse)
async def serachEmpl(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    userdoc = user.to_dict()
# pull the form containing our data
    form = await request.form()
    targetCategory=form['options']
    userlocation = form['location']
    userdoc['location']=userlocation
    userID=user.id
    firestore_db.collection('users').document(userID).set(userdoc)
    employees =[]
    usersref = firestore_db.collection('users').where('field','==',targetCategory).get()
    for oneuser in usersref:
        if oneuser.get('avail')=='Active':
            employees.append(oneuser)
    
    
    sortedEmployees = sort_objects_by_distance(userlocation,employees)
    return templates.TemplateResponse('searchResult.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user,'employees':sortedEmployees})

#hire employee
@app.post("/hireEmpl", response_class=HTMLResponse)
async def hireEmpl(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    hire_ref = firestore_db.collection('hirings').document()
    id = hire_ref.id    
# set the data on the object
    hire_ref.set({
        'id':hire_ref.id,
        'userName':user.get('name'),
        'userEmail': user.get('email'),
        'date': datetime.now(),
        'emplEmail': form['email'],
        'emplLocation':form['emplLocation'],
        'userLocation':user.get('location'),
        'status':"Pending",
        'otp':"",
        'note':form['note']
    })

    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    return templates.TemplateResponse('userHiringReq.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':hiringReq})

#hiring accepted by employee - employee side
@app.post("/acceptJob", response_class=HTMLResponse)
async def acceptJob(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    id = form['reqid']
    otp = random.randint(1000, 9999)
    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    for doc in hiringReq:
        oneReq = doc.to_dict()
        userID = doc.id
        oneReq['status']="Accepted"
        oneReq['otp']=otp
        firestore_db.collection('hirings').document(userID).set(oneReq)

    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    return templates.TemplateResponse('emplJob.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':hiringReq})

#hiring rejected by employee
@app.post("/rejectJob", response_class=HTMLResponse)
async def rejectJob(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    id = form['reqid']
    hiringReqs = firestore_db.collection('hirings').where('id','==',id).get()
    # Iterate through the query results and delete the document(s)
    for hiringReq in hiringReqs:
        hiringReq.reference.delete()

    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#Start work by user
@app.post("/startWork", response_class=HTMLResponse)
async def startWork(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    id = form['reqid']
    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    for doc in hiringReq:
        oneReq = doc.to_dict()
        userID = doc.id
        oneReq['status']="Started"
        oneReq['jobStartTime']=datetime.now(pytz.UTC)
        firestore_db.collection('hirings').document(userID).set(oneReq)

    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    return templates.TemplateResponse('userHiringReq.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':hiringReq})

#Start work by user
@app.post("/finishWork", response_class=HTMLResponse)
async def finishWork(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    id = form['reqid']
    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    cost=0
    for doc in hiringReq:
        emplEmail= doc.get('emplEmail')
        employee= firestore_db.collection('users').where('email','==',emplEmail).get()
        for oneEmpl in employee:
            hrCharge=oneEmpl.get('hrCharge')
            wallet = oneEmpl.get('walletAddress')
        
        oneReq = doc.to_dict()
        userID = doc.id
        oneReq['status']="Finished"
        
        oneReq['jobEndTime']=datetime.now(pytz.UTC)
        duration= (datetime.now(pytz.UTC) - doc.get('jobStartTime')).total_seconds() / 3600
        oneReq['duration']= (datetime.now(pytz.UTC) - doc.get('jobStartTime')).total_seconds() / 3600
        cost = float(hrCharge) * float(duration)
        oneReq['totalCost']= math.ceil(cost)
        oneReq['emplWallet']=wallet
        if 'amount' in doc.to_dict():
            oneReq['totalCost'] = doc.get('amount')

        firestore_db.collection('hirings').document(userID).set(oneReq)


    
    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    return templates.TemplateResponse('userHiringReq.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':hiringReq,'cost':cost,'wallet':wallet})

#G2 token payment
@app.post("/cryptoPay", response_class=HTMLResponse)
async def cryptoPay(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    id = form['id']
    emplWallet = form['wallet']
    cost = form['cost']

    
    
    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    return templates.TemplateResponse('cryptoPay.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':hiringReq,'cost':cost,'wallet':emplWallet})


#posting a job for bidding by user
#hire employee
@app.post("/postJob", response_class=HTMLResponse)
async def postJob(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    hire_ref = firestore_db.collection('jobs').document()
    id = hire_ref.id    
# set the data on the object
    hire_ref.set({
        'id':hire_ref.id,
        'userName':user.get('name'),
        'userEmail': user.get('email'),
        'date': datetime.now(),
        'jobtype': form['options'],
        'Location':form['location'],
        'deadline':form['deadline'],
        'maxBudget':form['maxbudget'],
        'note':form['note'],
        'status':"Pending",
        'otp':"",
        'biddings':[]
    })

    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#new bid by employee
@app.post("/newBid", response_class=HTMLResponse)
async def newBid(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the form containing our data
    form = await request.form()
    bid = {
        'emplEmail':form['emplEmail'],
        'bidAmount':form['bidAmount']
    }
    user_doc_ref = firestore_db.collection('jobs').where('id','==',form['jobid']).get()
    for doc in user_doc_ref:
        biddings = doc.get('biddings')
        oneJob = doc.to_dict()
        jobID = doc.id
        biddings.append(bid)
        oneJob['biddings']=biddings
        firestore_db.collection('jobs').document(jobID).set(oneJob)

    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#View biddings for posted job by user
@app.post("/viewBids", response_class=HTMLResponse)
async def viewBids(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    id = form['jobid']
    jobs = firestore_db.collection('jobs').where('id','==',id).get()
    return templates.TemplateResponse('UserViewBids.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'jobs':jobs})

#grandin one bid by user
@app.post("/grandBid", response_class=HTMLResponse)
async def grandBid(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    user = getUser(user_token).get()
# pull the form containing our data
    form = await request.form()
    jobs = firestore_db.collection('jobs').where('id','==',form['jobid']).get()
    job=jobs[0]
    hire_ref = firestore_db.collection('bidWins').document()
    id = hire_ref.id    
# set the data on the object
    hire_ref.set({
        'id':hire_ref.id,
        'userName':user.get('name'),
        'userEmail': user.get('email'),
        'date': job.get('date'),
        'jobtype': job.get('jobtype'),
        'Location':job.get('Location'),
        'deadline':job.get('deadline'),
        'amount':form['bidAmount'],
        'note':job.get('note'),
        'status':"win",
        'otp':"",
        'emplEmail':form['emplEmail']
    })
    # Iterate through the retrieved documents and delete them
    for job in jobs:
        job.reference.delete()
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#starting win job by employee - employee side    working on this ````````````````````````````````````````````
@app.post("/startWinWork", response_class=HTMLResponse)
async def startWinWork(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    
# pull the form containing our data
    form = await request.form()
    
    jobid = form['jobid']
    otp = random.randint(1000, 9999)
    winjob = firestore_db.collection('bidWins').where('id','==',jobid).get()
    oneJob = winjob[0]

    hire_ref = firestore_db.collection('hirings').document()
    id = hire_ref.id    
# set the data on the object
    hire_ref.set({
        'id':hire_ref.id,
        'userName':oneJob.get('userName'),
        'userEmail': oneJob.get('userEmail'),
        'date': datetime.now(),
        'emplEmail': form['emplEmail'],
        'emplLocation':"",
        'userLocation':oneJob.get('Location'),
        'status':"Accepted",
        'otp':otp,
        'note':oneJob.get('note'),
        'amount': form['amount']
    })
    hiringReq = firestore_db.collection('hirings').where('id','==',id).get()
    for doc in winjob:
        doc.reference.delete()
    return templates.TemplateResponse('emplJob.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user, 'hiringReq':hiringReq})





@app.post("/buyG2", response_class=HTMLResponse)
async def buyG2(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    

    return templates.TemplateResponse('buyG2.html',{'request': request,'user_token': user_token,'error_message': 'error_message', 'user_info':user})

#After payment
@app.post("/allDone", response_class=HTMLResponse)
async def allDone(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    form = await request.form()
    
    reqid = form['id']
    rating = form['rating']
    emplEmail=''
    hiringReq = firestore_db.collection('hirings').where('id','==',reqid).get()
    for doc in hiringReq:
        emplEmail = doc.get('emplEmail')
        doc.reference.delete()
    employee = firestore_db.collection('users').where('email','==',emplEmail).get()
    for doc in employee:
        oneEmpl= doc.to_dict()
        userID = doc.id
        oldRating =doc.get('rating')
        ratingArr=doc.get('ratingArr')
        if oldRating == []:
            oneEmpl['ratingArr']=[rating]
            oneEmpl['rating']=rating
        else:
            count=0
            sum=0
            for i in ratingArr:
                count=count+1
                sum=sum+int(i)
            avg=(sum+int(rating))/(count+1)
            oneEmpl['rating']= avg
            ratingArr.append(rating)
            oneEmpl['ratingArr'] = ratingArr
            

    firestore_db.collection('users').document(userID).set(oneEmpl)


    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/stopwaiting", response_class=HTMLResponse)
async def stopwaiting(request: Request):

# there should be a token. Validate it and if invalid then redirect back to / as a basic security meas
    id_token = request. cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    user = getUser(user_token).get()
    form = await request.form()
    
    reqid = form['reqid']
    hiringReq = firestore_db.collection('hirings').where('id','==',reqid).get()
    for doc in hiringReq:
        doc.reference.delete()
    
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)