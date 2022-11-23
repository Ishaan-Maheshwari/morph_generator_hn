#!/bin/sh
i=1
while [ $i -le 362 ]
do
    python3 generate_input_modularize_new.py verified_sent/$i > log.txt
    i=$(($i+1))
done
