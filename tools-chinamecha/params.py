# coding: utf-8
import argparse

CMDINFO = {
    "version": '0.0.1',
    "description": "机电一体化网供应商信息采集",
    "epilog": """
使用案例:
    %(prog)s -l
    %(prog)s -t 电机 通信线 -T 20
    %(prog)s -T 10 --loglevel warning
    """,
    'params': {
        'DEFAULT': [
            {
                'name': ['-t', '--type'],
                'help': '类型',
                'dest': 'typename',
                'nargs': '+'
            },
            {
                'name': ['-l', '--list'],
                'dest': 'isShowlist',
                'help': '全部类型',
                'default': False,
                'action': 'store_true'
            },
            {
                'name': ['-T', '--thread'],
                'help': '线程数',
                'dest': 'thread_num',
                'type': int,
            },
            {
                'name': ['-r', '--range'],
                'help': '采集范围',
                'dest': 'range',
            },
        ],
    }
}

