# coding: utf-8
import argparse

CMDINFO = {
    "version": '0.0.1',
    "description": "好大夫在线医生信息采集",
    "epilog": """
使用案例:
    %(prog)s -p 31 -n fukezonghe
    """,
    'params': {
        'DEFAULT': [
            {
                'name': ['-p', '--province'],
                'help': '省份',
                'dest': 'province',
                'default': 'all',
            },
            {
                'name': ['-n', '--name'],
                'help': '科室名称',
                'dest': 'typename',
                'required': True,
            },
            {
                'name': ['-t', '--thread'],
                'help': '进程数量',
                'dest': 'thread_num',
                'default': 0,
                'type': int
            },
        ],
    }
}

