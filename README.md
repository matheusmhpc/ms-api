# ms-api
# Respostas pedidas:
1 - Migrar o front pro Heroku (DNS me ajudar)
Não sei nada sobre heroku
Acredito que basta deletar a entrada que tem de robo.rconsistence.com
Adicionar entrada CNAME apontando pra que eles informam

2  - Passo a Passo para criar um acesso no servidor
Basta acessar por SSH e fazer procedimento normal pra dar acesso por SSH em um servidor (modificando authorized_keys)

3 - Passo a passo para verificar logs (ms-api / ms-docker / containers). Eu vi a questão do CloudWatch, é possível colocarmos lá para facilitar? 
ms-api = docker logs ms-api
ms-docker = systemctl status ms-docker
containers = docker ps
log de um container = docker logs {nome do container}

Talvez tenha mas nunca usei dessa forma
O ideal seria um painel administrativo com todas as infos

4 - Comandos do docker que voce precisou usar e considera importante para algum momento (Ex. Matar todos os container)

Não existe comando para matar todos e mesmo se existisse não seria usado pois o ms-api é um container e o registry também
PARAR = docker stop {nome do container}
REMOVER = docker rm {nome do container}

Talvez não seja necessário remover pois o container é iniciado com um auto-remove

5 - Programas para facilitar o acesso e verificar log

Acessar por SSH e usar instruções de log
Caso queira acessar algum container algum dia basta usar "docker exec -it {nome do container} /bin/sh"
Esse passo anterior não é comumente usado!!
