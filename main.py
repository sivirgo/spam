import os
import configparser, traceback, json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except:
    os.system("pip install --upgrade pip")
    os.system("pip install requests")
    import requests

try:
    from websocket import create_connection
except:
    os.system("pip install websocket-client")
    from websocket import create_connection

try:
    from fake_useragent import UserAgent
except:
    os.system("pip install fake-useragent")
    from fake_useragent import UserAgent

jsondb = "db.johnson"

def login(nomor, password):
    try:
        ua = UserAgent()
        uafix = ua.random
        headers = {
            "User-Agent": uafix,
            "origin": "https://www.spooncast.net",
            "referer": "https://www.spooncast.net/",
            "content-type": "application/json"
        }
        jsons = {
            "device_unique_id": uafix,
            "auth_data": {
                "act_type": "phone",
                "password": password,
                "msisdn": nomor
            }
        }
        tokens = requests.post("https://id-auth.spooncast.net/tokens", headers=headers, json=jsons).json()
        jwt = tokens["data"]["jwt"]
        rtokenvalue = tokens["data"]["refresh_token"]

        #update headers dengan pair key baru
        headers["Authorization"] = "Bearer "+jwt

        jsonlogin = {
            "sns_type" : "phone",
            "sns_id" : nomor,
            "password" : password
        }
        login = requests.post("https://id-api.spooncast.net/signin/?version=2", headers=headers, json=jsonlogin).json()
        print(login)
        uid = str(login["results"][0]["id"])
        uname = login["results"][0]["nickname"]
        utag = login["results"][0]["tag"]
        config = {}

        config["nomor"] = nomor
        config["password"] = password
        config["uid"] = uid
        config["uname"] = utag
        config["utag"] = uname
        config["uafix"] = uafix
        config["jwt"] = jwt
        config["rtokenvalue"] = rtokenvalue

        with open(jsondb, "w") as jsonFile:
            json.dump(config, jsonFile, indent=2)

        print("berhasil login")
        return 1

    except:
        print(traceback.format_exc())
        print(tokens)
        print("id/password akun salah atau diban")
        return 0


def reqacc(config, slink):
    try:
        headers = {
            "Authorization": "Bearer " + config["jwt"],
            "User-Agent": config["uafix"],
            "origin": "https://www.spooncast.net",
            "referer": "https://www.spooncast.net/",
            "accept": "application/json",
            "host": "id-api.spooncast.net",
        }
        reqacc = requests.get("https://id-api.spooncast.net/lives/"+slink+"/access/", headers=headers).json()
    except:
        pass
def konek(config, slink, nickdj, title, k):
    try:
        ver = "10.5.7"
        rid = slink
        uid = config["uid"]
        jwt = config["jwt"]

        ws = create_connection("wss://id-heimdallr.spooncast.net/" + slink,
                               header={'User-Agent': 'Mozilla/5.0'})

        print("room rank " + str(k + 1)+'\n'+nickdj+'\n'+title)

        print(slink)

        first = '{"live_id":"' + rid + '","appversion":"' + ver + '","user_id":' + uid + ',"event":"live_state","type":"live_req","useragent":"Web"}'
        ws.send(first)
        time.sleep(1)
        second = '{"live_id":"' + rid + '","appversion":"' + ver + '","retry":0,"token":"Bearer ' + jwt + '","event":"live_join","type":"live_req","useragent":"Web"}'
        ws.send(second)
        health = '{"live_id":"' + rid + '","appversion":"' + ver + '","user_id":' + uid + ',"event":"live_health","type":"live_rpt","useragent":"Web"}'
        leave = '{"live_id":"' + rid + '","appversion":"' + ver + '","token":"Bearer ' + jwt + '","event":"live_leave","type":"live_rpt","useragent":"Web"}'

        j = 0
        while j == 0:

            try:
                s = ws.recv()
            except:
                j = 1
                ws.close()
                #print(traceback.format_exc())
            #print(s)
            chat = json.loads(s)
            try:
                evn = chat['event']
                if evn == "live_join":
                    cing = '{"message":"'+pesan+'","appversion":"' + ver + '","useragent":"Web","token":"Bearer ' + jwt + '","event":"live_message","type":"live_rpt"}'
                    ws.send(cing)
                    ws.send(leave)
                    ws.close()
                elif evn == "live_health":
                    ws.send(health)

            except Exception as e:
                #print('ini error bawah definisi')
                #print(traceback.format_exc())
                pass

    except Exception as e:
        print(e)
        print("error")
        print(traceback.format_exc())

if __name__ == '__main__':
    jbl = configparser.ConfigParser()
    jbl.read("config.ini")
    nomor = jbl["Spoon"]["nomor"].replace("08", "628")
    password = jbl["Spoon"]["password"]
    pesan = str(jbl["Spoon"]["pesan"][:99])
    maxroom = int(jbl["Spoon"]["max"])


    print(pesan)
    print(len(pesan))
    print(type(pesan))


    livedata = []

    ref = login(nomor, password)
    if ref == 0:
        print("id/password salah atau akun diban . silahkan ganti akun")
        exit()

    with open(jsondb, "r") as jsonFile:
        config = json.load(jsonFile)

    print("fetching data ...")

    try:
        listliveid = requests.get('https://id-api.spooncast.net/lives/popular/?page_size=30&is_adult=0').json()
        next = listliveid["next"]

        for k in range(len(listliveid["results"])):
            if len(livedata) == maxroom:
                break
            else:
                slink = str(listliveid['results'][k]['id'])
                title = str(listliveid['results'][k]['title'])
                nickdj = listliveid['results'][k]['author']['nickname']
                livedata.append((slink, title, nickdj))

        while (len(livedata) != maxroom):
            listliveid = requests.get(next).json()
            next = listliveid["next"]
            for k in range(len(listliveid["results"])):
                if len(livedata) == maxroom:
                    break
                else:
                    slink = str(listliveid['results'][k]['id'])
                    title = str(listliveid['results'][k]['title'])
                    nickdj = listliveid['results'][k]['author']['nickname']
                    livedata.append((slink, title, nickdj))
    except:
        pass
        #print(traceback.format_exc())

    print("fetch data complete")
    print("proses berjalan ...")

    processes = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for k in range(len(livedata)):
            slink = str(livedata[k][0])
            title = str(livedata[k][1])
            nickdj = livedata[k][2]
            time.sleep(1)
            try:
                reqacc(config, slink)
            except:
                pass
            processes.append(executor.submit(konek, config, slink, nickdj, title, k))
