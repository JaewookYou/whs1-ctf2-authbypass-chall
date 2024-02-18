#-*-coding:utf-8-*-
import flask
import os, pymysql, re, hashlib, time, base64, io, requests, datetime
import uuid, random, hashlib
import logging, traceback
logging.basicConfig(level=logging.INFO)
logging.getLogger('werkzeug').setLevel(level=logging.WARNING)
from threading import Lock

app = flask.Flask(__name__)
app.secret_key = os.urandom(16)
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024

FLAG = os.getenv("FLAG") or r"flag{testflag}"

messages = {}
admin_acctno = ""

lock = Lock()
def get_connection():
    return pymysql.connect(
        host='db',
        user='user',
        password='asdfasdf',
        database='chall',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def db_select(query, param):
    with lock:
        print(f"[+] db_select query - {query % param}")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, param)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"[x] select err.. {query} - {param}")
            return False
        finally:
            connection.close()

    return False

def db_insert(query, param):
    with lock:
        print(f"[+] db_insert query - {query % param}")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, param)
                connection.commit()
        except Exception as e:
            print(f"[x] insert err.. {query} - {param}")
            return False
        finally:
            connection.close()

def db_update(query, param):
    with lock:
        print(f"[+] db_update query - {query % param}")
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, param)
                connection.commit()
        except Exception as e:
            print(f"[x] update err.. {query} - {param}")
            return False
        finally:
            connection.close()


def sessionCheck(loginCheck=False):   
    if loginCheck:
        if "isLogin" not in flask.session:
            return False
        else:
            return True

    if "isLogin" in flask.session:
        return True
    
    return False

def getmyinfo(userseq):
    query = 'select * from users where userseq=%s'
    query_result = db_select(query,(userseq,))
    if query_result:
        return query_result[0]


@app.route("/api/get_sms_msg", methods=["GET"])
def get_sms_msg():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))
    
    phonenum = flask.request.args["phonenum"]
    if phonenum != flask.session["login_info"]["phonenum"]:
        return "x"

    if phonenum in messages:
        if len(messages[phonenum]):
            msg = messages[phonenum].pop(0)
            return msg
    
    return "x"

@app.route("/api/send_authmsg", methods=["GET"])
def send_authmsg():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    authnum = str(random.randint(0, 999999)).rjust(6,'0')
    
    phonenum = flask.request.args["phonenum"]
    
    if phonenum not in messages:
        messages[phonenum] = []
    
    messages[phonenum].append(authnum)
    messages[f"{phonenum}_auth"] = authnum

    if messages[phonenum]:
        return "send success"
    else:
        return "send false"


@app.route("/")
def index():
    if sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("my"))

    return flask.redirect(flask.url_for("login"))


@app.route("/login", methods=["GET","POST"])
def login():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("my"))
        
        return flask.render_template("login.html", msg="false")
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("my"))
        
        userid = flask.request.form["userid"]
        userpw = hashlib.sha256(flask.request.form["userpw"].encode()).hexdigest()
        
        query = 'select * from users where userid=%s and userpw=%s'
        query_result = db_select(query,(userid,userpw))
        
        if query_result:
            if query_result[0]["userid"] == userid:
                flask.session["userid"] = userid
                flask.session["isLogin"] = True
                flask.session["login_info"] = query_result[0]
                flask.session.modified = True
                print(f"[+] {userid} login success! {query_result[0]}")
                    
                resp = flask.make_response(flask.redirect(flask.url_for("my")))
                resp.set_cookie('userid', flask.session["userid"])
                if userid == "admin":
                    pass
                return resp

        else:
            return flask.render_template("login.html", msg="login fail")


@app.route("/login_simplepass", methods=["GET","POST"])
def login_simplepass():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("my"))
        
        return flask.render_template("login_simplepass.html", msg="false")
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("my"))
        
        simplepass_key = flask.request.form["simplepass_key"]
        simplepass = hashlib.sha256(flask.request.form["simplepass"].encode()).hexdigest()
        
        query = 'select * from users where simplepass_key=%s and simplepass=%s'
        query_result = db_select(query,(simplepass_key,simplepass))
        
        if query_result:
            if query_result[0]["simplepass_key"] == simplepass_key:
                flask.session["userid"] = query_result[0]["userid"]
                flask.session["isLogin"] = True
                flask.session["login_info"] = query_result[0]
                print(f"[+] {flask.session['userid']} login success! {query_result[0]}")
                    
                resp = flask.make_response(flask.redirect(flask.url_for("my")))
                resp.set_cookie('userid', flask.session["userid"])
                if flask.session["userid"] == "admin":
                    pass
                return resp

        else:
            return flask.render_template("login_simplepass.html", msg="login fail")


@app.route("/register", methods=["GET","POST"])
def register():
    if flask.request.method == "GET":
        if sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("my"))
        
        return flask.render_template("register.html", msg="false")
    else:
        if sessionCheck():
            return flask.redirect(flask.url_for("my"))

        userid = flask.request.form["userid"] 
        userpw = hashlib.sha256(flask.request.form["userpw"].encode()).hexdigest()

        while True:
            phonenum = f"018-{str(random.randint(0, 9999)).rjust(4,'0')}-{str(random.randint(0, 9999)).rjust(4,'0')}"

            query = 'select count(*) as count from users where phonenum=%s'
            query_result = db_select(query,(phonenum,))
            
            if query_result[0]['count'] > 0:
                print(f"[x] {phonenum} is duplicated")
            elif query_result[0]['count'] == 0:
                flask.session["phonenum"] = phonenum
                break
            else:
                print(f"[?] {query_result}")
        
        query = 'select count(*) as count from users where userid=%s'
        query_result = db_select(query,(userid,))
        
        if query_result[0]['count'] > 0:
            return flask.render_template("register.html", msg="already registered id")

        while True:
            acctno = str(uuid.uuid4())
            query = "select count(*) as count from users where acctno = %s"
            result = db_select(query, (acctno,))
            if result[0]['count'] == 0:
                break

        query = "insert into users (userid, userpw, phonenum, acctno, balance) VALUES (%s, %s, %s, %s, %s)"
        param = (userid, userpw, phonenum, acctno, 10000)
        if db_insert(query, param) == False:
            return flask.render_template("login.html", msg=f"db insert error")    

        # insert transaction
        transaction_date = datetime.datetime.now()
        query = "insert into transactions (from_address, to_address, amount, transaction_date) value (%s, %s, %s, %s)"
        param = (db_select("select acctno from users where userseq=100000",())[0]["acctno"], acctno, 10000, transaction_date)
        if db_insert(query, param) == False:
            return flask.render_template("login.html", msg=f"이체 오류")

        query = 'select count(*) as count from users where userid=%s'
        query_result = db_select(query,(userid,))

        if query_result[0]['count'] == 0:
            return flask.render_template("login.html", msg="register error")
        else:
            return flask.render_template("login.html", msg="false")
        

@app.route("/logout")
def logout():
    flask.session.pop('isLogin', False)
    resp = flask.make_response(flask.redirect(flask.url_for("login")))
    resp.set_cookie('userid', expires=0)
    return resp


@app.route("/my", methods=["GET"])
def my():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))
    
    if "userseq" in flask.request.args:
        userseq = flask.request.args["userseq"]
    else:
        userseq = flask.session["login_info"]["userseq"]

    return flask.render_template("my.html", login_info=getmyinfo(userseq))

@app.route("/mysms", methods=["GET"])
def mysms():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))
    
    
    return flask.render_template("mysms.html", login_info=flask.session["login_info"])    


@app.route("/smsauth", methods=["GET","POST"])
def smsauth():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    if flask.request.method == "GET":
        return flask.render_template("smsauth.html", msg="false", login_info=flask.session["login_info"])
    else:
        userid = flask.request.form["userid"]
        phonenum = flask.request.form["phonenum"]
        authnum = flask.request.form["authnum"]

        if messages[f"{phonenum}_auth"] == authnum:
            flask.session["2factor_success"] = True
            print("auth success")
            return flask.redirect(flask.url_for("register_simplepass"))
        else:
            flask.session["2factor_success"] = False
            print("auth fail")
            return flask.render_template("smsauth.html", msg="SMS 인증 실패", login_info=flask.session["login_info"])


@app.route("/register_simplepass", methods=["GET","POST"])
def register_simplepass():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    if "2factor_success" in flask.session:
        if not flask.session["2factor_success"]:
            return "<script>alert('SMS인증이 수행되지 않았습니다');location='/smsauth'</script>"
    else:
        return flask.redirect(flask.url_for("smsauth"))

    if flask.request.method == "GET":
        return flask.render_template("register_simplepass.html", msg="false", login_info=flask.session["login_info"])
    else:
        simplepass1 = flask.request.form["simplepass1"]
        simplepass2 = flask.request.form["simplepass2"]
        if simplepass1 != simplepass2:
            returnmsg = "비밀번호 확인이 일치하지 않습니다"
            return f"<script>alert('{returnmsg}');history.go(-1);</script>"

        if len(simplepass1) != 6:
            returnmsg = "비밀번호가 6자리가 아닙니다"
            return f"<script>alert('{returnmsg}');history.go(-1);</script>"            

        try:
            int(simplepass1)
        except:
            returnmsg = "비밀번호가 숫자가 아닙니다"
            return f"<script>alert('{returnmsg}');history.go(-1);</script>"

        simplepass = hashlib.sha256(simplepass1.encode()).hexdigest()
        simplepass_key = bytes.hex(os.urandom(32))

        userid = flask.request.form["userid"]

        query = "update users set simplepass=%s, simplepass_key=%s where userid=%s"
        param = (simplepass, simplepass_key, userid)
        if db_update(query, param) == False:
            return "<script>alert('간편비밀번호 등록 오류');history.go(-1);</script>"

        returnmsg = f"{userid} 간편비밀번호 등록 완료"
        flask.session["2factor_success"] = None

        return f"<script>alert('{returnmsg}');localStorage.setItem('simplepass_key','{simplepass_key}');location='/my';</script>"
    


@app.route("/transfer", methods=["GET","POST"])
def board():
    if flask.request.method == "GET":
        if not sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("login"))

        return flask.render_template("transfer.html", login_info=getmyinfo(flask.session["login_info"]["userseq"]))
    else:
        if not sessionCheck(loginCheck=True):
            return flask.redirect(flask.url_for("login"))

        info = getmyinfo(flask.session["login_info"]["userseq"])

        from_address = info["acctno"]
        to_address = flask.request.form["to_address"]
        amount = int(flask.request.form["amount"])
        transaction_date = datetime.datetime.now()

        nowamount = int(info["balance"])
        
        if amount > nowamount:
            returnmsg = "현재 잔액보다 이체할 금액이 큽니다"
            return f"<script>alert('{returnmsg}');history.go(-1);</script>"

        if amount > 1000000000:
            returnmsg = "1000000000 이상 이체할 수 없습니다"
            return f"<script>alert('{returnmsg}');history.go(-1);</script>"            

        query = "select balance from users where acctno=%s"
        param = (to_address, )
        query_result = db_select(query, param)
            
        if query_result:
            toamount = int(query_result[0]["balance"])
            print(f"[+] 받을계좌 {to_address} 잔액 : {toamount}")
        else:
            returnmsg = "이체할 대상 계좌가 존재하지 않습니다"
            return f"<script>alert('{returnmsg}');history.go(-1);</script>"

        # sub money
        query = "update users set balance=%s where acctno=%s"
        param = (nowamount-amount, from_address)
        if db_update(query, param) == False:
            return "<script>alert('이체 오류');history.go(-1);</script>"

        # add money
        query = "update users set balance=%s where acctno=%s"
        param = (toamount+amount, to_address)
        if db_update(query, param) == False:
            return "<script>alert('이체 오류');history.go(-1);</script>"

        # insert transaction
        query = "insert into transactions (from_address, to_address, amount, transaction_date) value (%s, %s, %s, %s)"
        param = (from_address, to_address, amount, transaction_date)
        if db_insert(query, param) == False:
            return "<script>alert('이체 오류');history.go(-1);</script>"

        return flask.redirect(flask.url_for("my"))

@app.route("/transfer_history", methods=["GET"])
def transfer_history():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    address = flask.session["login_info"]["acctno"]
    query = "select * from transactions where from_address=%s or to_address=%s"
    param = (address, address)
    query_result = db_select(query, param)
    
    if query_result:
        transactions = []
        for r in query_result:
            t = {}
            t["transaction_id"] = r["transaction_id"]
            t["amount"] = r["amount"]
            t["transaction_date"] = r["transaction_date"]

            acctno = r["from_address"]
            query = "select * from users where acctno=%s"
            param = (acctno,)
            query_result2 = db_select(query,param)
            if query_result2:
                t["from_address"] = r['from_address']
                t["from_id"] = query_result2[0]['userid']

            acctno = r["to_address"]
            query = "select * from users where acctno=%s"
            param = (acctno,)
            query_result2 = db_select(query,param)
            if query_result2:
                t["to_address"] = r['to_address']
                t["to_id"] = query_result2[0]['userid']

            transactions.append(t)


        return flask.render_template("transfer_history.html", transactions=transactions)
    else:
        return flask.render_template("transfer_history.html", transactions=[])
    

@app.route("/getflag")    
def getflag():
    if not sessionCheck(loginCheck=True):
        return flask.redirect(flask.url_for("login"))

    if getmyinfo(flask.session["login_info"]["userseq"])["balance"] > 1000000000:
        return FLAG


if __name__ == "__main__":

    while 1:
        try:
            get_connection()
            break
        except:
            print("[x] wait db...")
            time.sleep(3)

    # init
    query = 'select count(*) as count from users where userid=%s'
    query_result = db_select(query,("admin",))
    
    if query_result[0]['count'] == 0:
        print("[+] make admin account..")

        userid = "admin"
        userpw = "asdfasdf"
        phonenum = "99999999"
        acctno = str(uuid.uuid4())
        balance = 10000000000000000
        query = "insert into users (userid, userpw, phonenum, acctno, balance) VALUES (%s, %s, %s, %s, %s)"
        param = (userid, userpw, phonenum, acctno, balance)
        db_insert(query, param)

        admin_acctno = acctno

        print(f"[+] admin acctno : {acctno}")

    try:
        app.run(host="0.0.0.0", port=9001, debug=True)
    except Exception as ex:
        logging.info(str(ex))
        pass
