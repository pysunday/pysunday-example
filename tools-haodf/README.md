# 安装插件

该插件依赖[sunday](https://github.com/pysunday/pysunday), 需要先安装sunday

执行sunday安装目录：`sunday_install tools-haodf`

## zhipin命令使用

```bash
 $ haodf_doctor -h
usage: haodf_doctor [-v] [-h] [-p PROVINCE] -n TYPENAME [-t THREAD_NUM]

好大夫在线医生信息采集

Optional:
  -v, --version                       当前程序版本
  -h, --help                          打印帮助说明
  -p PROVINCE, --province PROVINCE    省份
  -n TYPENAME, --name TYPENAME        科室名称
  -t THREAD_NUM, --thread THREAD_NUM  进程数量

使用案例:
    haodf_doctor -p 31 -n fukezonghe
```
