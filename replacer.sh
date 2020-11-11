#/bin/sh

##File to replace variables where needed

BucketName=$1
filePath=$2

fileName=$(basename $filePath)
#echo $fileName
pwd

if [ $fileName == "redshift_data_lifecycle_management_cf.json" ]; then
  sed -i '' "s/REPLACEBUCKETNAME/$BucketName/g" "$filePath"
fi

if [ $fileName == "validator.py" ]; then
  sed'' "s/dir_Name_Var/validator\./g" $filePath > validator/validator/$fileName
  sed'' "s/dir_Name_Var//g" $filePath > src/lambdas/$fileName
fi