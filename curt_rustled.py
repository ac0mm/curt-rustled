#!/usr/bin/python3

import getpass
import sys
import cmd
import socket
import os
import paramiko #type: ignore
from impacket.smbconnection import SMBConnection #type: ignore
from impacket.dcerpc.v5 import transport, scmr #type: ignore
from impacket.dcerpc.v5.dtypes import NULL #type: ignore

# Define necessary constants
SC_MANAGER_ALL_ACCESS = 0xF003F
SERVICE_ALL_ACCESS = 0xF01FF
SERVICE_WIN32_OWN_PROCESS = 0x00000010
SERVICE_DEMAND_START = 0x00000003
SERVICE_ERROR_IGNORE = 0x00000000



class windows_smb(cmd.Cmd):

    intro = 'SMB interactive shell with Impacket'
    prompt = '(smb)> '

    def __init__ (self):

        super().__init__()
        self.smb_connection = None
        self.dce = None
        self._connect_smb()

    def _connect_smb(self):

        ip = input("What is the remote host ip?: ")
        domain = input("What is the remote host's domain?: ")
        username = input("what is the username for the remote host?: ")
        password = getpass.getpass("What is the password?: ")

        try:
            self.smb_connection = SMBConnection(ip, ip)
            self.smb_connection.login(username, password, domain)

            rpctransport = transport.SMBTransport(ip, filename='\\svcctl', smb_connection=self.smb_connection)
            self.dce = rpctransport.get_dce_rpc()
            self.dce.connect()
            self.dce.bind(scmr.MSRPC_UUID_SCMR) #type: ignore

            print("Connected to remote host.")
        
        except Exception as e:
            print(f"Connection error: {e}")
            sys.exit(1)

    def do_run(self, arg):
        'Run a command on the remote machine: run <command>'

        try:
            command = f"cmd.exe /c {arg}"
            self._execute_remote_command(command)
            print(f"Executed command: {arg}")
        
        except Exception as e:
            print(f"Error executing Command: {e}")

    def _execute_remote_command(self, command):

        try:
            # Open SCManager
            resp = scmr.hROpenSCManagerW(self.dce, NULL, NULL, SC_MANAGER_ALL_ACCESS)
            scManagerHandle = resp['lpScHandle']

            # Create Service
            resp = scmr.hRCreateServiceW(
                self.dce,
                scManagerHandle,
                'myservice',               # Service Name
                'My Test Service',         # Display Name
                command,                   # Binary Path
                SERVICE_WIN32_OWN_PROCESS,  # Service Type
                SERVICE_DEMAND_START,      # Start Type
                SERVICE_ERROR_IGNORE,      # Error Control
                NULL,                      # Load Order Group
                NULL,                      # Tag ID
                NULL,                      # Dependencies
                NULL,                      # Service Start Name
                NULL                       # Password
            )
            serviceHandle = resp['lpServiceHandle']

            # Start Service
            scmr.hRStartServiceW(self.dce, serviceHandle)
            scmr.hRDeleteService(self.dce, serviceHandle)
            scmr.hRCloseServiceHandle(self.dce, serviceHandle)
            scmr.hRCloseServiceHandle(self.dce, scManagerHandle)
        except Exception as e:
            print(f"Error in _execute_remote_command: {e}")
            raise


    def do_exit(self, arg):
        'Exit the shell'

        if self.dce:
            self.dce.disconnect()
        if self.smb_connection:
            self.smb_connection.logoff()
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

        ip = input("What is the IP of the remote host?: ")
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
            sock.connect((ip,port))

            #create a paramiko transport
            self.transport = paramiko.Transport(sock)
            
            if password:
                self.transport.connect(username=user, password=password)

            elif sshkey:
                private_key = paramiko.RSAKey.from_private_key_file(sshkey)
                self.transport.connect(username=user, pkey=private_key)

            os.makedirs(ip, exist_ok=True)

        except Exception as e:

            print(f"Error: {e}")
            if self.transport:
                self.transport.close()
            if sock:
                sock.close()
            quit()            

    def do_run(self, arg):

        if self.transport is None:
            self.transport_none()

        try:
            session = self.transport.open_session()
            session.exec_command(arg)
            stdout = session.makefile('r', -1)
            
            try:
                print(stdout.read().decode())
            except Exception as e:
                print(f"Error: {e}")
            
            session.close()

        except Exception as e:
            print(f"Error: {e}")

    def do_survey(self, arg):

        survey_commands = [ 'id', 'set', 'env', 'ps -ef', 'netstat -tuna', 'ls -latr', 'ls -latr /']

        for command in survey_commands:

            if self.transport is None:
                self.transport_none()
            
            try:
                session = self.transport.open_session()
                session.exec_command(command)
                stdout = session.makefile('r', -1)
            
                try:
                    print(stdout.read().decode())
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
        remoteType = input("SSH to linux or SMB?: ")
        if remoteType == "SMB" or remoteType == "smb":
            shell = windows_smb()
            shell.cmdloop()
            break
        elif remoteType == "SSH" or remoteType == "ssh":
            shell = linux_ssh()
            shell.cmdloop()
            break
        elif remoteType == "exit" or remoteType == "quit":
            quit()
        else:
            print("Not a valid option, please select ssh, smb, exit or quit")