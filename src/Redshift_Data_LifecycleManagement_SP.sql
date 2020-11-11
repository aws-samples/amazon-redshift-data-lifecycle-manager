create or replace procedure SCHEMAVARIABLE.rs_data_lc_manager(schema_name IN varchar(32), table_name IN varchar(32), col_name IN varchar(32), gran_level IN varchar(8), ret_period IN int, s3_path IN varchar(256), file_format IN varchar(128),partition_column IN varchar(32), role_name IN varchar(256), region_name IN varchar(256), max_filesize IN varchar(16), parallel_flag IN varchar(16), update_delete_flag IN int, checkpoint IN varchar(32), days_out_count OUT int, rows_out_count OUT int, checkpoint_out_date OUT varchar(32))
AS $$
DECLARE
    days_count INT;
    months_count INT;
    rows_count BIGINT;
    checkpoint_date VARCHAR(32);
BEGIN
IF gran_level = 'daily' 
THEN
	IF checkpoint = 'None'
	THEN
		EXECUTE 'SELECT count(distinct ' || col_name || '),count(1),max(' || col_name || ') from '  || schema_name || '.' || table_name || ' where ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)' INTO days_count, rows_count,checkpoint_date;
    	days_out_count:=days_count; 
    	rows_out_count:=rows_count;
		checkpoint_out_date:=checkpoint_date;
    ELSE
    	EXECUTE 'SELECT count(distinct ' || col_name || '),count(1),max(' || col_name || ') from '  || schema_name || '.' || table_name || ' where ' || col_name || ' > ''' || checkpoint || ''' and ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)' INTO days_count, rows_count,checkpoint_date;
    	days_out_count:=days_count; 
    	rows_out_count:=rows_count;
    	checkpoint_out_date:=checkpoint_date;
    END IF;
    IF update_delete_flag = 0
    THEN
    	IF checkpoint = 'None'
    	THEN 
    		EXECUTE  'unload (''select * from ' || schema_name || '.' || table_name || ' where ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)'') to ''' || s3_path || ''' iam_role ''' || role_name || ''' ' || file_format || partition_column || ' ALLOWOVERWRITE REGION ''' || region_name || ''' ' || parallel_flag || ' MAXFILESIZE ' || max_filesize ||'';
    		RAISE INFO 'Moved % days(s) of data comprising % row(s)', days_count, rows_count;
    	ELSE
    		EXECUTE  'unload (''select * from ' || schema_name || '.' || table_name || ' where ' || col_name || ' > ''''' || checkpoint || ''''' and ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)'') to ''' || s3_path || ''' iam_role ''' || role_name || ''' ' || file_format || partition_column || ' ALLOWOVERWRITE REGION ''' || region_name || ''' ' || parallel_flag || ' MAXFILESIZE ' || max_filesize ||'';
    		RAISE INFO 'Moved % days(s) of data comprising % row(s)', days_count, rows_count;
    	END IF;
    ELSIF update_delete_flag = 1
    THEN
    	EXECUTE  'delete from ' || schema_name || '.' || table_name || ' where ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)';
    	RAISE INFO 'Deleted % days(s) of data comprising % row(s)', days_count, rows_count;
    ELSIF update_delete_flag = 2
    THEN
    	EXECUTE  'unload (''select * from ' || schema_name || '.' || table_name || ' where ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)'') to ''' || s3_path || ''' iam_role ''' || role_name || ''' ' || file_format || partition_column || ' ALLOWOVERWRITE REGION ''' || region_name || ''' ' || parallel_flag || ' MAXFILESIZE ' || max_filesize ||'';
    	RAISE INFO 'Moved % days(s) of data comprising % row(s)', days_count, rows_count;
    	EXECUTE  'delete from ' || schema_name || '.' || table_name || ' where ' || col_name || ' < dateadd(day,-' || ret_period || ',current_date)';
    	RAISE INFO 'Deleted % days(s) of data comprising % row(s)', days_count, rows_count;
    ELSE
    	RAISE EXCEPTION 'Invalid update_delete_flag value';
    END IF;
ELSIF gran_level = 'monthly'
THEN
	IF checkpoint = 'None'
	THEN
		EXECUTE 'SELECT count(distinct date_trunc(''month'',' || col_name || ')),count(1),max(trunc(date_trunc(''month'',' || col_name || '))) from '  || schema_name || '.' || table_name || ' where date_trunc(''month'',' || col_name || ') < add_months(date_trunc(''month'',current_date),-' || ret_period || ')' INTO months_count, rows_count,checkpoint_date;
		days_out_count:=months_count; 
    	rows_out_count:=rows_count;
		checkpoint_out_date:=checkpoint_date;
    ELSE
    	EXECUTE 'SELECT count(distinct date_trunc(''month'',' || col_name || ')),count(1),max(trunc(date_trunc(''month'',' || col_name || '))) from '  || schema_name || '.' || table_name || ' where date_trunc(''month'',' || col_name || ') > ''' || checkpoint || ''' and date_trunc(''month'',' || col_name || ') < add_months(date_trunc(''month'',current_date),-' || ret_period || ')' INTO months_count, rows_count, checkpoint_date;
		days_out_count:=months_count; 
    	rows_out_count:=rows_count;
    	checkpoint_out_date:=checkpoint_date;
    END IF;
    IF update_delete_flag = 0
    THEN
    	IF checkpoint = 'None'
    	THEN
    		EXECUTE  'unload (''select * from ' || schema_name || '.' || table_name || ' where date_trunc(''''month'''',' || col_name || ') < add_months(date_trunc(''''month'''',current_date),-' || ret_period || ')'') to ''' || s3_path || ''' iam_role ''' || role_name || ''' ' || file_format ||  partition_column || ' ALLOWOVERWRITE REGION ''' || region_name || ''' ' || parallel_flag || ' MAXFILESIZE ' || max_filesize ||'';
    		RAISE INFO 'Moved % month(s) of data comprising % row(s)', months_count, rows_count;
    	ELSE
    		EXECUTE  'unload (''select * from ' || schema_name || '.' || table_name || ' where date_trunc(''''month'''',' || col_name || ') > ''''' || checkpoint || ''''' and date_trunc(''''month'''',' || col_name || ') < add_months(date_trunc(''''month'''',current_date),-' || ret_period || ')'') to ''' || s3_path || ''' iam_role ''' || role_name || ''' ' || file_format || partition_column || ' ALLOWOVERWRITE REGION ''' || region_name || ''' ' || parallel_flag || ' MAXFILESIZE ' || max_filesize ||'';
    		RAISE INFO 'Moved % month(s) of data comprising % row(s)', months_count, rows_count;
    	END IF;
    ELSIF update_delete_flag = 1
    THEN
    	EXECUTE  'delete from ' || schema_name || '.' || table_name || ' where date_trunc(''month'',' || col_name || ') < add_months(date_trunc(''month'',current_date),-' || ret_period || ')';
    	RAISE INFO 'Deleted % month(s) of data comprising % row(s)', months_count, rows_count;
    ELSIF update_delete_flag = 2
    THEN
    	EXECUTE  'unload (''select * from ' || schema_name || '.' || table_name || ' where date_trunc(''''month'''',' || col_name || ') < add_months(date_trunc(''''month'''',current_date),-' || ret_period || ')'') to ''' || s3_path || ''' iam_role ''' || role_name || ''' ' || file_format || partition_column || ' ALLOWOVERWRITE REGION ''' || region_name || ''' ' || parallel_flag || ' MAXFILESIZE ' || max_filesize ||'';
    	RAISE INFO 'Moved % month(s) of data comprising % row(s)', months_count, rows_count;
    	EXECUTE  'delete from ' || schema_name || '.' || table_name || ' where date_trunc(''month'',' || col_name || ') < add_months(date_trunc(''month'',current_date),-' || ret_period || ')';
    	RAISE INFO 'Deleted % month(s) of data comprising % row(s)', months_count, rows_count;
    ELSE
    	RAISE EXCEPTION 'Invalid update_delete_flag value';  
    END IF;  	
ELSE
	RAISE EXCEPTION 'Incorrect arguments';
END IF;
EXCEPTION
  WHEN OTHERS THEN
    RAISE INFO 'Exception Occured';
END;
$$
LANGUAGE plpgsql
;


