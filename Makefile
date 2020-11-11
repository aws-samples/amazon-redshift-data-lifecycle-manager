create:
	@read -p "Enter S3 Bucket Name: " BucketName; \
	mkdir -p build; \
	cp cftemplate/redshift_data_lifecycle_management_cf.json build/; \
	chmod 755 replacer.sh; \
	./replacer.sh $$BucketName build/redshift_data_lifecycle_management_cf.json; \
	./replacer.sh $$BucketName config/validator.py; \
	cd src/lambdas/; \
	zip -q ../../build/csv_dydb_writer.zip dynamo_writer.py; \
	zip -qr ../../build/csv_dydb_writer.zip validator.py; \
	pip3 install --upgrade -r ../../requirements.txt -t . --ignore-installed; \
	zip -q ../../build/redshiftProcedureCreation.zip redshift_manager.py; \
	zip -qr ../../build/redshiftProcedureCreation.zip pg8000*; \
	zip -qr ../../build/redshiftProcedureCreation.zip scramp*; \
	cd ../../; \
	aws s3 cp config/validator-0.1-py3.6.egg s3://$$BucketName/redshift-data-lifecycle-manager/config/; \
	aws s3 cp build/csv_dydb_writer.zip s3://$$BucketName/redshift-data-lifecycle-manager/config/; \
	aws s3 cp build/redshiftProcedureCreation.zip s3://$$BucketName/redshift-data-lifecycle-manager/config/; \
	aws s3 cp src/glue/management_job.py s3://$$BucketName/redshift-data-lifecycle-manager/config/; \
	aws s3 cp src/Redshift_Data_LifecycleManagement_SP.sql s3://$$BucketName/redshift-data-lifecycle-manager/config/; \
	aws s3 cp sample/test_configuration.csv s3://$$BucketName/redshift-data-lifecycle-manager/sample/; \
	aws s3 cp build/redshift_data_lifecycle_management_cf.json s3://$$BucketName/redshift-data-lifecycle-manager/; \
	region=$(shell aws configure get region); \
	echo "CloudFormation deployment URL"; \
	echo "https://console.aws.amazon.com/cloudformation/home?region=$$region#/stacks/new?stackName=redshift-data-lc-util&templateURL=https://$$BucketName.s3.amazonaws.com/redshift-data-lifecycle-manager/redshift_data_lifecycle_management_cf.json"

clean:
	rm -rf build
	rm -f src/glue/validator.py
	rm -f validator/validator/validator.py

validate:
	rm -rf validator/dist; \
	rm -rf validator/build; \
	rm -rf validator.egg-info; \
	mkdir -p validator/validator; \
	cp -f config/dataclasses.py validator/validator/; \
	cp -f config/setup.py validator/; \
	cp -f config/__init__.py validator/validator/; \
	cd validator; \
	pyenv local 3.6.0; \
	python3.6 setup.py bdist_egg; \
	cd ../; \
	rm -rf config/validator-0.1-py3.6.egg; \
	cp validator/dist/validator-0.1-py3.6.egg config/

build: clean validate create

