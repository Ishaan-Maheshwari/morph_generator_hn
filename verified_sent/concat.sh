i=1
while [ $i -le 358 ]
do 
    cat $i >> file_out.txt
    echo "$i is added"
    i=$(($i+1))
done
