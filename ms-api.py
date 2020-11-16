import boto3
import os
import requests
import functools
from flask_restful import Resource, Api, abort
from flask import Flask, jsonify, request, Response
from flask_cors import CORS, cross_origin
import json
from waitress import serve
from ansi2html import Ansi2HTMLConverter
import datetime

conv = Ansi2HTMLConverter()

awsip = '172.31.'

actions = []
microservices = []
cacherunning = {}
lastrunnew = datetime.datetime.now()
class YClass(object):
    pass

settings = YClass()

setattr(settings, 'AWS_SERVER_PUBLIC_KEY', 'AKIAZIUW4JWP6MN32EN2')
setattr(settings, 'AWS_SERVER_SECRET_KEY', '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')

setattr(settings, 'AWS_SERVER_PUBLIC_KEY_EC2', 'AKIAZIUW4JWP5FTOTDLV')
setattr(settings, 'AWS_SERVER_SECRET_KEY_EC2', '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')

setattr(settings, 'REGION_NAME', 'sa-east-1')
setattr(settings, 'CONTAINER_PREFIX', 'RCONSIST-')
setattr(settings, 'LOGIN_API', 'https://login.mathz.dev/')
setattr(settings, 'LOGIN_API', 'https://rconsistence-microservice.herokuapp.com')

setattr(settings, 'MY_IP', '172.31.8.238')

setattr(settings, 'RUNNING_NEW', False)
setattr(settings, 'MIN_AVAILABLE', 2)

app = Flask(__name__)
CORS(app)
api = Api(app)
UPLOAD_FOLDER = "uploads"
BUCKET = "rconsistence-bot-files"

session = boto3.Session(
    aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
    aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY,
    region_name=settings.REGION_NAME
)

ec2 = boto3.resource('ec2',
                      aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY_EC2,
                      aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY_EC2,
                      region_name=settings.REGION_NAME
                      )

ec22 = boto3.client('ec2',
                      aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY_EC2,
                      aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY_EC2,
                      region_name=settings.REGION_NAME
                      )

s3_client = boto3.client('s3',
                      aws_access_key_id=settings.AWS_SERVER_PUBLIC_KEY,
                      aws_secret_access_key=settings.AWS_SERVER_SECRET_KEY,
                      region_name=settings.REGION_NAME
                      )

def run_new_machine():
    returno = ec22.run_instances(ImageId='ami-084c7571b19a3031a',
                      MinCount=1,
                      MaxCount=1,
                      InstanceType='t2.micro',
                      SecurityGroupIds=[
                          'sg-0b17ffee0da577e77',
                      ],
                      UserData='sudo apt update -y && sudo apt install apt-transport-https ca-certificates curl software-properties-common -y && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable" && sudo apt update -y && apt-cache policy docker-ce && sudo apt install docker-ce -y && sudo usermod -aG docker ubuntu && sudo systemctl enable docker && sudo systemctl start docker && sudo apt install python3-pip && pip3 install boto3 && pip3 install flask && pip3 install flask-restful && pip3 install docker && pip3 install requests && chmod +x /opt/ms-docker.py && systemctl start ms-docker && systemctl enable ms-docker && docker ps'
                      )

def verify_to_run():
    global lastrunnew
    letsgo = False
    free = 0
    date = datetime.datetime.now()
    if (lastrunnew < date):

        for each in microservices:
            link = 'http://' + each + '/status'
            status = requests.get(link)
            json = status.json()
            running = int(json.get("running"))
            max = int(json.get("max"))
            free = free + (max - running)


        if (free < 2):
            letsgo = True

        if(letsgo):
            date = date + datetime.timedelta(minutes=2)
            lastrunnew = date
            run_new_machine()

def stop_machine(ip):
    running_instances = ec2.instances.filter(Filters=[{
        'Name': 'instance-state-name',
        'Values': ['running']}])

    id = None
    if(ip != settings.MY_IP):
        for instance in running_instances:
            if (instance.private_ip_address == ip):
                id = instance.id
                break

        if (id != None):
            ec2.instances.filter(InstanceIds=id).stop()
            ec2.instances.filter(InstanceIds=id).terminate()

def verify_machine(ip):
    free = 0
    global microservices
    for each in microservices:
        try:
            link = 'http://' + each + '/status'
            status = requests.get(link, timeout=3)
            json = status.json()
            running = int(json.get("running"))
            max = int(json.get("max"))
            free += (max - running)
        except:
            pass

    link = 'http://' + ip + '/status'
    status = requests.get(link)
    json = status.json()

    running = int(json.get("running"))
    max = int(json.get("max"))

    free = free - (max - running)

    if ((running == 0) and (free > 1)):
        microservices.remove(ip)
        ip = ip.split(':')
        ip = ip[0]
        stop_machine(ip)

def get_all_microservices():
    global microservices
    bkp = []
    for i in range (254):
        for j in range (254):
            ip = awsip+str(i)+'.'+str(j)
            timeout = 0.3
            link = 'http://' + ip + '/alive'
            status = requests.get(link, timeout=timeout)
            if(status.status_code == 200):
                bkp.append(ip)
    microservices = bkp

def save_cache(machine, force):
    global cacherunning
    date = datetime.datetime.now()
    if (force != True):
        try:
            cache = cacherunning[machine]
            if (date < cache['datetime']):
                return (False)
        except:
            pass
    try:
        link = 'http://' + machine + '/all'
        status = requests.get(link, timeout=3)
        date = date + datetime.timedelta(minutes=1)
        data = status.json()
        data = data['containers']
        obj = {'datetime': date,
               'containers': data}
        cacherunning[machine] = obj
        return (True)

    except:
        date = date + datetime.timedelta(minutes=5)
        obj = {'datetime': date,
               'containers': []}
        cacherunning[machine] = obj

def get_docker_ip(id):
    choosed = False
    for machine in microservices:
        save_cache(machine, False)
    id = str(id)
    containername = settings.CONTAINER_PREFIX + id
    print (cacherunning)
    for each in cacherunning:
        if containername in cacherunning[each]['containers']:
            choosed = each

    """link = 'http://' + each + '/find'
    status = requests.get(link, json={'id': id})

    if (status.status_code != 200):
        choosed = False"""

    return (choosed)

def get_docker_ip_old(id):
    choosed = False
    for ip in microservices:
        link = 'http://' + ip + '/find'
        status = requests.get(link, json={'id': id})
        if (status.status_code == 200):
            choosed = ip
            break
    return (choosed)

def get_free_ip():
    choosed = False

    for ip in microservices:
        print(ip)
        link = 'http://' + ip + '/status'
        status = requests.get(link)
        json = status.json()
        max = json.get("max")
        running = json.get("running")

        if (int(max) > int(running)):
            choosed = ip
            break

    return (choosed)

def run_container(id, token):
    ip = get_free_ip()
    if(ip):
        link = 'http://' + ip + '/run'
        status = requests.post(link, json={'id': id,
                                           'token': token})
        save_cache(ip, True)
        return (status)
    else:
        return (False)

def get_container_logs(id):
    ip = get_docker_ip(id)
    if(ip):
        link = 'http://'+ip+'/log'
        logs = requests.get(link, json={'id': id})
        save_cache(ip, False)
        return (logs)
    else:
        return (False)

def stop_container(id):
    ip = get_docker_ip(id)
    if(ip):
        link = 'http://' + ip + '/stop'
        status = requests.post(link, json={'id': id})
        save_cache(ip, True)
        return (status.status_code)
    else:
        return (False)

def login_required(method):
    @functools.wraps(method)
    def wrapper(self):
        user = {}
        try:
            header = request.headers.get('Authorization')
            _, token = header.split()
        except:
            token = header
            #abort(401, message='Error (A1): Token is not valid.')

        if(token):
            header = {
                'Authorization': header
            }
            urlme = settings.LOGIN_API+'/me'
            answer = requests.get(urlme, headers=header)

            """try:
                user = answer.json
                try:
                    user = user.decode("utf-8")
                except:
                    pass
            except:"""
            user = answer.content
            user = user.decode("utf-8")
            user = json.loads(user)
            try:
                id = user["user"]["id"]
            except:
                abort(401, message='Error (A2): contact admin.')

            return method(self, user)
        else:
            abort(401, message='Error (A3): contact admin.')
        return method(self, user)
    return wrapper

def upload_file(file_name, bucket, id, name):
    """
    Function to upload a file to an S3 bucket
    """
    id = str(id)
    object_name = UPLOAD_FOLDER+'/'+id+'/'+name
    #s3_client = boto3.client('s3')
    response = s3_client.upload_file(file_name, bucket, object_name)
    return response

class upload_sinais(Resource):
    @login_required
    def post(self, user):
        id = user.get("user").get("id")
        f = request.files['file']
        filename = 'sinais'
        f.save(os.path.join(UPLOAD_FOLDER, str(id)+'-'+filename))
        upload_file(f"uploads/{str(id)}-{filename}", BUCKET, id, 'sinais')
        return "Upload do arquivo de sinais realizado com sucesso!", 201

class upload_config(Resource):
    @login_required
    def post(self, user):
        id = user.get("user").get("id")
        status = get_docker_ip(id)
        if (status):
            return "Não é possível modificar configurações enquanto o bot estiver executando!", 409
        f = request.files['file']
        filename = 'config'
        f.save(os.path.join(UPLOAD_FOLDER, str(id)+'-'+filename))
        upload_file(f"uploads/{str(id)}-{filename}", BUCKET, id, 'config')
        return "Upload do arquivo de configuração realizado com sucesso!", 201

class run_script(Resource):
    @login_required
    def post(self, user):

        header = request.headers.get('Authorization')
        _, token = header.split()

        id = user.get("user").get("id")
        status = run_container(id, token)
        if(status):
            verify_to_run()
            return Response("Programa executando!", status=status.status_code)
        else:
            return Response("Falha ao tentar executar!", status=406)

class stop_script(Resource):
    @login_required
    def post(self, user):
        global cacherunning
        id = user.get("user").get("id")
        status = stop_container(id)
        if(status == 200):
            for each in actions:
                if (each['id'] == id):
                    each['active'] = False
                    actions.remove(each)
            id = str(id)
            containername = settings.CONTAINER_PREFIX + id
            for each in cacherunning:
                if containername in cacherunning[each]['containers']:
                    cacherunning[each]['containers'].remove(containername)

            return Response("Programa parado!", status=status)
        else:
            return Response("Falha ao tentar parar!", status=406)

class get_logs(Resource):
    @login_required
    def get(self, user):
        id = user.get("user").get("id")
        status = get_container_logs(id)
        toconvert = status.content.decode("utf-8")
        retorno = conv.convert(toconvert)
        #retorno = ansi_to_html(toconvert)
        if (status):
            return Response(retorno, status=status.status_code)
        else:
            return Response("Falha ao tentar pegar o log de " + user.get("email") + '!', status=406)

class get_running(Resource):
    @login_required
    def get(self, user):
        id = user.get("user").get("id")
        id = str(id)
        status = get_docker_ip(id)
        if(status):
            retorno = {'status': True}
        else:
            retorno = {'status': False}
        return jsonify(retorno)

class i_am_online(Resource):
    def post (self):
        global microservices
        try:
            #print(request.environ)
            try:
                ip = request.environ['HTTP_X_REAL_IP']
            except:
                ip = request.environ['REMOTE_ADDR']
            #print(ip)
            port = request.json['port']
            #print(port)
            port = str(port)
            #print(port)
            machine = ip+':'+port
            #print(machine)
            if (machine not in microservices):
                microservices.append(machine)
            return Response("Cadastrado!", status=200)
        except:
            abort(400, message='Falhou')

class cad_action(Resource):
    def post (self):
        try:
            obj = request.json
            obj['active'] = True
            obj['id'] = str(obj['id'])
            if (obj not in actions):
                actions.append(obj)
            return Response("Cadastrado!", status=200)
        except:
            abort(400, message='Falhou')

class has_action(Resource):
    @login_required
    def get(self, user):
        print(actions)
        id = user.get("user").get("id")
        id = str(id)
        obj = {'status': False,
               'message': '',
               'title': ''}

        for each in actions:
            if ((each['id'] == id) and each['active']):
                obj['status'] = True
                obj['message'] = each['message']
                obj['title'] = each['title']

        return jsonify(obj)

class send_input(Resource):
    @login_required
    def post(self, user):
        global actions
        id = user.get("user").get("id")
        id = str(id)
        message = request.json['message']
        machine = get_docker_ip(id)
        status = requests.post('http://'+machine+'/input', json={
            'id': id,
            'message': message
        })

        if (status.status_code == 200):
            for each in actions:
                if (each['id'] == id):
                    each['active'] = False
                    actions.remove(each)
            return Response(status.content, status=status.status_code)
        else:
            return Response("Falha ao tentar enviar a ação!", status=406)

class power_off(Resource):
    def post (self):
        global microservices
        try:
            ip = request.environ['HTTP_X_REAL_IP']
            port = request.json['port']
            port = str(port)
            machine = ip+':'+port
            verify_machine(machine)
            print("Máquina "+machine+"parada.")
            return Response("Máquina parada!", status=200)
        except:
            abort(400, message='Falhou')

class verify_power_off(Resource):
    def get (self):
        try:
            for each in microservices:
                verify_machine(each)
            return Response("Verificado!", status=200)
        except:
            abort(400, message='Falhou')

api.add_resource(run_script, '/run')
api.add_resource(stop_script, '/stop')
api.add_resource(get_logs, '/log')
api.add_resource(upload_sinais, '/sinais')
api.add_resource(upload_config, '/config')
api.add_resource(get_running, '/status')
api.add_resource(i_am_online, '/online')
api.add_resource(cad_action, '/actions')
api.add_resource(has_action, '/action')
api.add_resource(send_input, '/input')
api.add_resource(power_off, '/poweroff')
api.add_resource(verify_power_off, '/verifypoweroff')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
    #app.run(host="0.0.0.0", port=8080)
