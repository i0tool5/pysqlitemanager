# -*- coding: utf-8 -*-

import argparse
import os.path
import sqlite3
import sys

from subprocess import Popen, PIPE
from time import sleep


banner = '''

  ____        ____   ___  _     ___ _       __  __                                   
 |  _ \ _   _/ ___| / _ \| |   |_ _| |_ ___|  \/  | __ _ _ __   __ _  __ _  ___ _ __ 
 | |_) | | | \___ \| | | | |    | || __/ _ \ |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
 |  __/| |_| |___) | |_| | |___ | || ||  __/ |  | | (_| | | | | (_| | (_| |  __/ |   
 |_|    \__, |____/ \__\_\_____|___|\__\___|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|   
        |___/                                                        |___/           
'''

class DBWorker:
    def __init__(self, dbpath: str):
        self.dbconn = sqlite3.connect(dbpath)
        self.cursor = self.dbconn.cursor()

    def commit(self):
        self.dbconn.commit()

    def exec(self, statement: str):
        self.cursor.execute(statement)
        self.dbconn.commit()

    def retrieve(self) -> list:
        f = self.cursor.fetchall()
        return f

    def exit(self):
        self.dbconn.commit()
        self.dbconn.close()


def max_elem_len_by_col(arr: "two-dimensional list") -> dict:
    max_lengths = {}
    columns = [elem for elem in zip(*arr)] or None
    if columns is not None:
        for i in range(len(columns)):
            x = str(max(columns[i], key=lambda e: len(str(e))))
            max_lengths[i] = len(x)

    return max_lengths


def equalize_length(arr: "two-dimensional list") -> "two dimensional list":
    '''
    Will return two-dimensional list with centered, length-aligned, string typed elements inside e.g:
    >>> equalize_length([[12, '123', '1234'], ['123', 1, '12']])
    [[' 12', '123', '1234'], ['123', ' 1 ', ' 12 ']]
    '''
    out_list = []
    elem_len = max_elem_len_by_col(arr)
    for sub in arr:
        x = []
        for i in range(len(sub)):
            x.append(str(sub[i]).center(elem_len[i], " "))
        out_list.append(x)

    return out_list


def arg_work() -> ("method", argparse.Namespace):
    argparser = argparse.ArgumentParser(description="Connects to some SQLITE3 database and works with it in interactive mode.")
    argparser.add_argument("-d", "--dbpath", help="Path to database. If not specified `cmd` will require an imput of path")
    argparser.add_argument("-q", "--query", help="Run SQL query on specified database (-d is required)")
    argparser.add_argument
    usage = argparser.print_help
    namespace = argparser.parse_args()
    return usage, namespace


def cmd_exec(cmd: str):
    proc = Popen(["powershell", "-Command", cmd], stdout=PIPE, stderr=PIPE)
    p_out, p_err = proc.stdout, proc.stderr
    if p_out and p_out.readable():
        print(p_out.read().decode("cp1251"))
    if p_err and p_err.readable():
         print(p_err.read().decode("cp1251"))


def show_tables(dbconn: DBWorker, statmnt: str) -> None:
    additional = statmnt.replace("show tables", '')
    GET_TABLES = "SELECT * FROM sqlite_master{};".format(additional)
    dbconn.exec(GET_TABLES)
    tabs = dbconn.retrieve()

    for elem in tabs:
        full_sql_stmt = elem[-1]
        tabs_cols = full_sql_stmt.replace('CREATE TABLE ', '')
        tabs_cols = tabs_cols[:-1].split('(')
        print("[*] Table name: " + tabs_cols[0])
        print("[*] Columns: " + tabs_cols[1])


def db_work(db_path: str):
    
    INP = "sql#> "

    dbconn = DBWorker(db_path)
    SHOW_STMT = "show tables"
    EXIT_CMDS = ("q", "break", "exit", "close", "quit")
    
    while True:
        try:
            inp = input(INP)
            low_inp = inp.lower()
            if low_inp in EXIT_CMDS:
                dbconn.exit()
                print("\nBye!")
                break
            elif SHOW_STMT in low_inp:
                show_tables(dbconn, low_inp)
            elif inp.startswith('!'):
                cmd_exec(inp[1:])
            elif low_inp.startswith("select"):
                dbconn.exec(inp)
                fetched = dbconn.retrieve()
                selected_rows = []
                for elem in equalize_length(fetched):
                    data = ' | '.join([str(item) for item in elem])
                    selected_rows.append(data)
                
                max_strlen = len(max(selected_rows, key=len, default=[])) + 4 # -> 4 because of next print("|", row, "|") adds additional space characters
                print(" Fetched ".center(max_strlen, '_'))

                for row in selected_rows:
                    print("|", row, "|")
                    
                print(" Done ".center(max_strlen, '-'))                    
            elif not inp:
                pass
            else:
                dbconn.exec(inp)
                print("[*] OK!")
        except KeyboardInterrupt:
            dbconn.exit()
            print("\n\nBye!")
            break
        # except Exception as e:
        #     print("[EXCEPTION] `{}`".format(e))


def main():
    print(banner)
    usage, cmd_args = arg_work()
    
    if (path := cmd_args.dbpath) and not (quer := cmd_args.query):
        if os.path.exists(path):
            print("Welcome!\n") #😊
            db_work(path)
        else:
            print("[!] No such file: `{}`\nCreate? [y/N] ".format(path), end=' ')
            x = input()
            if x.lower().startswith('y'):
               print("[!] Working with new file: `{}`".format(path))
               db_work(path)
            else:
                print("Bye!") 
    elif (path := cmd_args.dbpath) != None and (quer := cmd_args.query):
        worker = DBWorker(path)
        worker.exec(quer)
        res = worker.retrieve()
        for i in res:
            print(' '.join([str(x) for x in i]))
        worker.exit()
    else:
        usage()


if __name__ == "__main__":
    main()