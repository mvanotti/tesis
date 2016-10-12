+++
categories = [
  "maxinet",
]
tags = [
  "doc",
]

title = "Correr test en Maxinet"
date = "2016-10-12T14:23:59-03:00"

+++

Una lista casi completa de los comandos necesarios para correr los tests en Maxinet

Compilar
===

Hay que compilar y subir el binario a la carpeta de rsk en `maxinet@maxihead`

~~~~
$scp binary.jar maxihead@maxinet:rsk
~~~~

Topología
===

En la creación de la topología se usan los archivos `networktopo` y `main.go` (y hay uno para los logs)

Una topología con la configuración para 30 máquinas se puede crear con los comandos

~~~~
$python networktopo.py --n=30`
$go run main.go -n 30 -m 12 -minP 5 -maxP 10 -txs 0`
~~~~

Para copiar los archivos al server usamos `rsync`

~~~~
$rsync -ua NetworkTopo maxinet@maxihead:rsk
$rsync -ua configs maxinet@maxihead:rsk
$rsync -ua logsconfigs maxinet@maxihead:rsk
~~~~

Ya estamos listos para hacer `ssh` al server

En maxihead
===

Primero chequeamos que todo esté en orden con `ibstat`. Si las cosas están en orden seguimos. En caso de problemas difícilmente se arreglen de forma remota.

Luego seguramente vamos a querer attacharnos a `tmux` con `tmux a`. Los comandos más usados de `tmux` seguramente sean `ctrl+b w`, `ctrl+b c` y `ctrl+b d`. Consultar internet por más cosas.

Estando ahí recordamos que los nodos están en `host-file` que se usa en el alias `pssh` para hacer parrallel ssh a todas las pcs y así ejecutar un comando en todos los nodos a la vez.

Por ejemplo chequeamos un estado básico con

~~~~
$pssh -i uptime
~~~~

Estando en maxihead puede que querramos **matar todo**, **levantar datos viejos** o **correr nuevo experimento**.

Kill all
===

Para matar los workers y limpiar Mininet está el script `~/bin/stopmaxinetworker.sh`

~~~~
$pssh -i ~/bin/stopmaxinetworker
$pssh -i ~/bin/resetmininet.sh
~~~~

El controller y el frontend se matan con ctrl+c en la ventana correspondiente.

Si es necesario matar las instancias de rsk es un simple `killall`

~~~~
$pssh -i sudo killall java
~~~~

Limpiamos los logs viejos (por ahí podemos querer bajarlos antes)

~~~~
$pssh -i ~/bin/cleanlogs.sh`
~~~~

Correr experimentos
===

En una terminal de `tmux` levantamos el frontend

~~~~
$MaxiNetFrontendServer
~~~~

En otra levantamos el controller

~~~~
$java -jar floodlight.jar -cf floodlightdefault.properties
~~~~

Y en otra más levantamos los workers

~~~~
$pssh -i ~/bin/maxinetworker.sh
~~~~

Corremos el experimento

~~~~
$python maxinet-rsk.py
~~~~

Bajar data
===

En maxihead simplemente corremos

~~~~
$download.sh
~~~~

Extras
===

Para conectarnos a un nodos

~~~~
$ssh nodo
~~~~

Chequear que se esté minando o lo que sea

~~~~
$pssh -i tail /usr/tmp/<num>*log
~~~~

Generar gráfico

~~~~
$dot -Tpng connectivity.dot connectivity.png
~~~~

Generar los gráficos de métricas. Hay que juntar los logs en un archivo común, llamado consumado en este caso.

~~~~
$python3 main.py < consumado
~~~~

