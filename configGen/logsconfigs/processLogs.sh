#!/bin/bash

for i in $(seq 1 100)
do
	cp log4j.properties.1 log4j.properties.10.0.0.$i
	sed -i "s/10\.0\.0\.1/10\.0\.0\.$i/g" log4j.properties.10.0.0.$i
done
