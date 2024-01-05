# common tools by sunday

基于sunday的常用命令行工具包

## 依赖

1. 系统：Mac OS或者Linux OS
1. python：python3
2. 包管理器：pysunday

## pysunday介绍

pysunday是一个封装了登录态管理、多线程、日志系统等功能的敏捷开发库，他提供了非常丰富的api供外部敏捷开发python脚本，让脚本开发简单而又高效！

安装pysunday：`python3 -m pip install pysunday`

## 安装

使用sunday_install安装：`sunday_install git仓库地址`

## 命令

### `sd_getip`

返回当前网络的IP地址

示例：

```console
 $ sd_getip
192.168.1.3
```

### `sd_grepn`

封装grep命令，正则匹配当前目录文本，匹配结果带文本行号，且主动过滤目录node_modules、.git、dist、build、docs

**注意：转译需要用3个斜杠(\)`

示例：

```console
 $ sd_grepn \\\${pid}
.//sd_port:8:    echo 进程号\(pid\): ${pid}
```

### `sd_port`

查看端口是否被占用，如果占用则返回进程号、执行目录、执行命令

示例：

```console
 $ sd_port 3000
端口号(port)：3000
进程号(pid): 69571
执行命令：node --inspect-brk name.js
执行目录：/Users/user/path/to/name
```

### `sd_chrome`

命令行打开chrome浏览器，只支持mac系统

示例：

```console
# 打开浏览器并新建tab
$ sd_chrome
# chrome中打开指定网站
$ sd_chrome https://baidu.com
```

## 设置别名

在sh工具的配置文件中使用alias设置命令别名，如在`~/.zshrc`文件中写入：

```bash
alias getip=sd_getip
alias grepn=sd_grepn
alias chrome=sd_chrome
alias getport=sd_port
```

设置好后执行`source ~/.zshrc`让改动生效

