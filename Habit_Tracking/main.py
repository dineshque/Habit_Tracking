# -*- coding: utf-8 -*-
#basic imports
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request,Flask,redirect
from flask_login import LoginManager,login_user,login_required,logout_user,current_user
from datetime import datetime
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.dates import DateFormatter

#app initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quantified_self_database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.app_context().push()
app.config['SECRET_KEY']='myappquantified'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='/notfound/Unauthorized'
#database import
from database import *

#==============================Business Logic====================================
#------------Login-Logout-------------
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
#-------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        uname=request.form.get('username')
        passd=request.form.get('password')
        try:
            user=User.query.filter(User.username==uname,User.password==passd).one()
        except:
            return render_template('login.html',error='incorrect password or username')
        if not current_user.is_active:
            login_user(user)
    if current_user.is_active:
        return main()
    else:
        return render_template('login.html')
#---------------------------
@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        uname=request.form.get('username')
        passd=request.form.get('password')
        if uname not in [i.username for i in User.query.all()]:
            user=User(username=uname,password=passd)
            db.session.add(user)
            db.session.commit()
            return login()
        return redirect('/notfound/User already exists.')
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return login()
#---------------------Not found error ----------------
@app.route("/notfound/<error>")
def notfound(error):
    return render_template('notfound.html',error=error)

#-------------------Tracker---------------------------
@app.route('/main')
@login_required
def main():
    return render_template('main.html',user=current_user,datetime=datetime)

@app.route('/tracker/add',methods=['GET','POST'])
@login_required
def add_tracker():
    if request.method=='POST':
        u_id=current_user.get_id()
        name=request.form.get('name')
        desc=request.form.get('desc')
        type=request.form.get('type')
        set=request.form.get('settings')
        #---validation----
        if name in [i.name for i in User.query.get(u_id).trackers]:
            return notfound('Tracker name should be unique')

        if type=='Multiple-choice':
            if set=="":
                return notfound('Tracker setting not valid, Multi-Choice should have setting separated by comma.')
        elif set!="":
            set=""
        #-----------------
        add=tracker(user_id=u_id,name=name,desc=desc,type=type,settings=set)
        try:
            db.session.add(add)
            db.session.commit()
            return main()
        except Exception as e:
            db.session.rollback()
            return(f'-------add_tracker_db_error-------{e}')
    return render_template('add_tracker.html',user=current_user)

@app.route('/tracker/<int:tracker_id>',methods=['GET','POST'])
@login_required
def view_tl(tracker_id):
    #Validarion
    if (tracker_id,) not in db.session.query(tracker.tracker_id).all():
        return notfound('tracker_id_not_found')
    t=tracker.query.get(tracker_id)
    tl=log.query.filter(log.tracker_id==tracker_id).order_by(log.log_datetime)
    x,y=[],[]
    fig=plt.figure(figsize=(8,5))
    ax = fig.gca()
    if request.method=='POST' and request.form.get('period'):#to remove bug from direct function call
        p=request.form.get('period')
        if p=='Custom':
            llim=request.form['customdatetimel']
            hlim=request.form['customdatetimeh']
            comp='%Y-%m-%dT%H:%M'
        elif p=='Today':
            llim=datetime.today().strftime('%d/%m/%y')
            hlim=llim
            comp='%d/%m/%y'
        elif p=='1Month':
            llim=datetime.today().strftime('%m/%y')
            hlim=llim
            comp='%m/%y'
        elif p=='All':
            llim,hlim,comp='','',''
    else:
      llim,hlim,comp='','',''

    for i in tl:
        if i.log_datetime.strftime(comp)>=llim and i.log_datetime.strftime(comp)<=hlim:
            x.append(i.log_datetime)
            if t.type=='Integer':
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                plt.ylabel('Int')
                y.append(int(i.log_value))
            elif t.type=='Numeric':
                plt.ylabel('Float')
                y.append(float(i.log_value))
            elif t.type=='Multiple-choice':
                plt.ylabel('Options')
                y.append(i.log_value)
            elif t.type=='Time':
                ax.yaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
                y.append(datetime.strptime(i.log_value,"%H:%M:%S"))
    plt.plot(x,y,marker='o',color='b',linestyle='--')
    plt.gcf().autofmt_xdate()
    plt.savefig('static/chart.png')
    if len(x)>0:
        img='/static/chart.png'
    else:
        img=""
    return render_template('tracker.html',tracker=t,chart=img)

@app.route('/tracker/<int:tracker_id>/update',methods=['GET','POST'])
@login_required#*************************
def update_tracker(tracker_id):
    #Validarion
    if (tracker_id,) not in db.session.query(tracker.tracker_id).all():
        return notfound('tracker_id_not_found')
    t=tracker.query.get(tracker_id)
    if request.method=='POST':
        try:
            if request.form.get('name')!=t.name or request.form.get('desc')!=t.desc or request.form.get('type')!=request.form.get('settings'):
                db.session.query(log).filter(log.tracker_id==tracker_id).delete()
            updict={tracker.name:request.form['name'],tracker.desc:request.form['desc'],tracker.type:request.form['type'],tracker.settings:request.form['settings']}
            print(updict)
            db.session.query(tracker).filter(tracker.tracker_id==tracker_id).update(updict)
            db.session.commit()
            return main()
        except:
            print('-------------db_update_error--------------')
            db.session.rollback()

    return render_template('update_tracker.html',tracker=t,user=current_user)

@app.route('/tracker/<int:tracker_id>/delete',methods=['GET','POST'])
@login_required
def delete_tracker(tracker_id):
    #Validarion
    if (tracker_id,) not in db.session.query(tracker.tracker_id).all():
        return notfound('tracker_id_not_found')
    t=tracker.query.get(tracker_id)
    try:
        db.session.delete(t)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('----tracker_delete_dberror------',e)
    return main()
#-----------------------------logs---------------------------
@app.route('/<int:tracker_id>/log/add',methods=['GET','POST','PUT'])
@login_required
def add_logs(tracker_id): #
    #Validation
    if (tracker_id,) not in db.session.query(tracker.tracker_id).all():
        return notfound('tracker_id_not_found')
    t=tracker.query.get(tracker_id)
    #EndV
    if request.method=='POST':
        try:
            value=request.form.get('value')
            if t.type=='Time':
              check=datetime.strptime(value,'%H:%M:%S')
            log_datetime=datetime.strptime(request.form.get("time"),'%d/%b/%Y, %H:%M:%S.%f')
            if t.lastupdate==None or t.lastupdate<log_datetime:
                t.lastupdate=log_datetime
            l=log(tracker_id=tracker_id,log_datetime=log_datetime,note=request.form.get('note'),log_value=value)
            db.session.add(l)
            db.session.commit()
            return view_tl(tracker_id)
        except:
            db.session.rollback()
            print('-------------db_log_add_error--------------')
    timedict={'start':'','end':'','duration':''}
    if request.method=='GET':
        if request.args.get('start'):
            s=request.args.get('start')
        elif request.args.get('startb')=="start":
            s=datetime.now().strftime('%H:%M:%S')
        else:
            s=''
        if request.args.get('end'):
            e=request.args.get('end')
        elif request.args.get('endb')=="end":
            e=datetime.now().strftime('%H:%M:%S')
        else:
            e=''
        d=''
        if s!='' and e!='':
            d=datetime.strptime(e,'%H:%M:%S')-datetime.strptime(s,'%H:%M:%S')
        timedict={'start':s,'end':e,'duration':d}
    return render_template('add_logs.html',t=t,datetime=datetime,timedict=timedict)

@app.route('/<int:log_id>/log/update',methods=['GET','POST'])
@login_required
def update_log(log_id):#############more validation needed#######
    #validation
    if (log_id,) not in db.session.query(log.log_id).all():
        return notfound('log_id_not_found')
    l=log.query.get(log_id)
    #EndV
    if request.method=='POST':
        log_value=request.form.get("value")
        log_note=request.form.get("note")
        log_datetime=datetime.strptime(request.form.get("time"),'%d/%b/%Y, %H:%M:%S.%f')
        #print(log_datetime)
        db.session.query(log).filter(log.log_id==log_id).update({'log_value':log_value,'note':log_note,'log_datetime':log_datetime})
        db.session.commit()
        return view_tl(l.tracker_id)
    return render_template('update_logs.html',datetime=datetime,log=l)

@app.route('/<int:log_id>/log/delete',methods=['GET','POST'])
@login_required
def delete_log(log_id):
    #validation
    if (log_id,) not in db.session.query(log.log_id).all():
        return notfound('log_id_not_found')
    l=log.query.get(log_id)
    t=l.tracker_id
    db.session.delete(l)
    db.session.commit()
    return view_tl(t)
#====================================================================================

if __name__=='__main__':
    app.run()
