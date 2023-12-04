[![pipeline status](http://10.80.4.138:8251/root/reef/badges/devp/pipeline.svg)](http://10.80.4.138:8251/root/reef/commits/devp)
[![coverage report](http://10.80.4.138:8251/root/reef/badges/devp/coverage.svg)](http://10.80.4.138:8251/root/reef/commits/devp)
## 数据库配置

数据库名称: reef

数据库用户: postgres

数据库密码: postgres

## 更新记录

### 性能测试去掉广告时间

1. 数据库运行如下的sql语句：
```
ALTER TABLE apiv1_rds 
ADD COLUMN ads_start_point INT4, 
ADD COLUMN ads_end_point INT4, 
ADD COLUMN original_job_duration FLOAT8;
```