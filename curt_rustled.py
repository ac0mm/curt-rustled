#!/usr/bin/python3

import getpass
import sys
import cmd
import socket
import os
import paramiko #type: ignore
import time
import winrm #type: ignore
from package.logem import logem #type: ignore

class windows_winrm(cmd.Cmd):

    intro = 'Winrm interactive shell with pywinrm'
    prompt = f'(winrm)>'

    def __init__ (self):

        super().__init__()
        self.winrm_connection = None
        self._connect_winrm()

    def _connect_winrm(self):

        self.ip = input("What is the remote host ip?: ")
        username = input("What is the username?: ")
        password = getpass.getpass("What is the password?: ")

        try:
            self.winrm_connection = winrm.Session(self.ip, auth=(username, password))
            message = f"Connected to {self.ip} via winrm"
            logem('logs/curt_rustled.log', message, "info")
            logem(f'{self.ip}/logs/system.log', message, "info")

        except Exception as e:
            message = f"Error: {e}"
            logem('logs/error.log', message, "error")
            print(message)
            sys.exit(1)

        os.makedirs(self.ip, exist_ok=True)

    def do_run(self, arg):
        'Run a command on the remote machine: run <command>'

        if self.winrm_connection is None:
            sys.exit(1)

        try:
            message = f"Running command {arg}"
            logem(f'{self.ip}/logs/system.log', message, 'info')

            runit = self.winrm_connection.run_cmd(arg)
        
            try:
                message = runit.std_out.decode()
                print(message)
                logem(f'{self.ip}/logs/interactive.log', message, 'info')
            
            except Exception as e:
                print(f"Error: {e}")

        except Exception as e:
            logem('logs/error.log', f"{self.ip} Error: {e}", 'error')
            sys.exit(1)

    def do_survey(self, arg):

        survey_commands = [ 'whoami /all', 'pwd', 'systeminfo', 'ipconfig /all', 'tasklist /M', 'netstat /naob', 'dir', 'dir C:\\']

        for command in survey_commands:

            if self.winrm_connection is None:
                sys.exit(1)
            
            try:
                runit = self.winrm_connection.run_cmd(command)

                array = command.split()
                if array:
                    logcmd = array[0]

                if logcmd:
                    epochtime = int(time.time())
                    log = f'{logcmd}-{epochtime}.txt'
                    
                try:
                    message = runit.std_out.decode()
                    print(message)
                    logem(f'{self.ip}/survey/{log}', message, 'info')
                except Exception as e:
                    print(f"Error: {e}")

            except Exception as e:
                print(f"Error: {e}")

    def do_exit(self, arg):
        'Exit the shell'
        return True

class linux_ssh(cmd.Cmd):

    intro = 'SSH interactive shell'
    prompt = '(ssh)> '

    def __init__ (self):

        super().__init__()
        self.transport = None
        self._connect_ssh()

    def _connect_ssh(self):

        password = None
        sshkey = None

        self.ip = input("What is the ip of the remote host?: ")
        strport = input("What is the port ssh is listening on on the remote host?: ")
        user = input("What is the username you wish to use?: ")
        
        while True:
        
            p_or_k = input("Do you wish to use a key or a password?: ")
            if p_or_k == "key":
                sshkey = input("Please put the full path to the ssh key: ")
                break
            elif p_or_k == "password":
                password = getpass.getpass("What is the password?: ")
                break
            else:
                print("The options are key or password")

        port = int(strport)

        try:

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.ip,port))

            #create a paramiko transport
            self.transport = paramiko.Transport(sock)
            
            if password:
                self.transport.connect(username=user, password=password)
                message = f"Connected to {self.ip} via ssh with password"
                logem('logs/curt_rustled.log', message, "info")
                logem(f'{self.ip}/logs/system.log', message, "info")

            elif sshkey:

                try:
                    with open(sshkey, 'r') as key_file:
                        first_line = key_file.readline().strip()

                        if 'BEGIN RSA PRIVATE KEY' in first_line:
                            keytype = 'RSA'
                        elif 'BEGIN OPENSSH PRIVATE KEY' in first_line:
                            keytype = 'ECDSA'
                        else:
                            print('Unknown key type, exiting')
                            sys.exit(0)

                except Exception as e:

                    message = f'Error: {e}'
                    logem('logs/error.log', message, "error")
                    print("Error exiting")
                    sys.exit(1)

                if keytype == 'RSA':

                    private_key = paramiko.RSAKey.from_private_key_file(sshkey)

                elif keytype == 'ECDSA':

                    private_key = paramiko.ECDSAKey.from_private_key_file(sshkey)

                else:
                    print('Unknown key type, exiting')
                    exit(0)

                self.transport.connect(username=user, pkey=private_key)
                message = f"Connected to {self.ip} via ssh with ssh key"
                logem('logs/curt_rustled.log', message, "info")
                logem(f'{self.ip}/logs/system.log', message, "info")

            os.makedirs(self.ip, exist_ok=True)

        except Exception as e:

            message = f"Error: {e}"
            logem('logs/error.log', message, "error")
            print(message)
            if self.transport:
                self.transport.close()
            if sock:
                sock.close()
            quit()            

    def do_run(self, arg):

        if self.transport is None:
            self.transport_none()

        try:
            message = f"Running command {arg}"
            logem(f'{self.ip}/logs/system.log', message, 'info')
            session = self.transport.open_session()
            session.exec_command(arg)
            stdout = session.makefile('r', -1)
            
            try:
                message = stdout.read().decode()
                print(message)
                logem(f'{self.ip}/logs/interactive.log', message, 'info')
            except Exception as e:
                print(f"Error: {e}")
            
            session.close()

        except Exception as e:
            logem('logs/error.log', f"{self.ip} Error: {e}", 'error')

    def do_survey(self, arg):

        survey_commands = [ 'id', 'set', 'env', 'ps -ef', 'netstat -tuna', 'ls -latr', 'ls -latr /']

        for command in survey_commands:

            if self.transport is None:
                self.transport_none()
            
            try:
                session = self.transport.open_session()
                session.exec_command(command)
                stdout = session.makefile('r', -1)

                array = command.split()
                if array:
                    logcmd = array[0]

                if logcmd:
                    epochtime = int(time.time())
                    log = f'{logcmd}-{epochtime}.txt'
                    
                try:
                    message = stdout.read().decode()
                    print(message)
                    logem(f'{self.ip}/survey/{log}', message, 'info')
                except Exception as e:
                    print(f"Error: {e}")
                session.close()

            except Exception as e:
                print(f"Error: {e}")

    def do_exit(self, arg):
        if self.transport:
            self.transport.close()
            return True

if __name__ == '__main__':

    while True:
        remoteType = input("Please choose an option:\nSSH = Linux, WINRM = windows: ")
        if remoteType == "SSH" or remoteType == "ssh":
            shell = linux_ssh()
            shell.cmdloop()
            break
        elif remoteType == "winrm" or remoteType == 'WINRM':
            shell = windows_winrm()
            shell.cmdloop()
            break
        elif remoteType == "exit" or remoteType == "quit":
            quit()
        else:
            print("Not a valid option, please select ssh, winrm, exit or quit")
