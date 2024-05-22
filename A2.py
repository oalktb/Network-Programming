# -------------------------
# Network Programming and Applications
# Second Semester (2023-2024)
# Assignment 2
# -------------------------

# -------------------------
# Student Name: Omar Alkhatib
# Student ID  : 20200430
# -------------------------

from config import HOST, PORT, BUFFER, TIMEOUT, CONTROL_CMDS, SET1, SET2, SET3
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from time import sleep

Active_cmds = []
is_loaded = {'set1': False, 'set2': False, 'set3': False}


# ------------- Client -------------------

def format_client(filename, server_addr=(HOST, PORT)):
    # 1- - Creates and configures the client socket
    print('format(client):')
    client_socket = socket(AF_INET, SOCK_STREAM)
    print('|| socket created')
    client_socket.settimeout(TIMEOUT)
    print(f'|| timeout set to {TIMEOUT}')

    # 2- Loads the list of commands from the given file.
    commands_list=[]

    # 3- Initiates a connection with server.
    try:
        client_socket.connect(server_addr)
        print('|| connected to server')
        try:
            print(f'|| Loading file: {filename}')
            commands_list = _get_cmds(filename)
        except:
            print('!! Exception: _get_cmds: file not found')
            print(f'|| commands = {commands_list}')
            client_socket.shutdown(SHUT_RDWR)
            print('|| connection shutdown')
            client_socket.close()
            print('|| client socket closed\n')
            return
    except (TimeoutError, OSError, ConnectionRefusedError) as e:
        print(f'formate_client: {e}')
        client_socket.close()
        print('|| client socket closed')
        return
    print(f'|| commands = {commands_list}')

    # 4- Sends the list of commands to the server.
    _send_cmds(client_socket, commands_list)
    client_socket.shutdown(SHUT_RDWR)
    print('|| connection shutdown')
    client_socket.close()
    print('|| client socket closed\n')
    return


def _get_cmds(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    lines = [line.strip() for line in lines]
    commands = __group_cmds(lines)
    return commands


def __group_cmds(commands):
    grouped_cmds = []
    current_group = []

    for cmd in commands:
        if cmd.startswith('$') and cmd.endswith('$'):
            if current_group:
                grouped_cmds.append(current_group)
            current_group = [cmd]
        else:
            current_group.append(cmd)
    if current_group:
        grouped_cmds.append(current_group)

    return grouped_cmds


def _send_cmds(client_sock, commands):
   for group in commands:
       for cmd in group:
           client_sock.sendall(cmd.encode())
           print(f'<< {cmd}')
           if 'end' not in cmd:
               try:
                   flag = client_sock.recv(BUFFER).decode()
               except:
                   return

               if flag =='&':
                   continue
               elif 'see' in flag:
                   print(f'>> {flag}')
                   return
               else:
                   print(f'>> {flag}')
           else:
               print('>> see you again')
               return


# ------------- Server -------------------

def format_server(server_addr=(HOST, PORT)):
    print('format(server):')

    # 1- Creates the server socket.
    server_socket = socket(AF_INET, SOCK_STREAM)

    # 2- Configures the server socket.
    flag = _configure_server(server_socket, server_addr)
    if flag == -1:
        server_socket.close()
        print('|| server socket closed')
        return
    try:
        i=1
        while True:
            connection, _ = server_socket.accept()
            _handle_client(connection, i)
            i=i+1
    except TimeoutError:
        print('\n!! Exception: accept timeout')
        server_socket.close()
        print('|| server socket closed')
        return
    server_socket.close()
    print('|| server socket closed')


def _configure_server(server_sock, server_addr):
    print('|| server socket created')
    server_sock.settimeout(TIMEOUT)
    print(f'|| timeout set to {TIMEOUT}')
    print('|| SO_REUSADDER option is set')
    try:
        server_sock.bind(server_addr)
        print('|| successful bind')
    except OSError as e:
        print(f'!! Configuration_Server: {e}')
        return -1

    server_sock.listen(20)
    print(f'|| listening on port {PORT} ...')
    return 1


def _handle_client(conn, client_num):
    print(f'\n|| connected to client {client_num}')
    try:
        while True:
            cmd, arg_list = _recv_cmd(conn)
            print(f'>> {cmd}')
            for args in arg_list:
                print(f'>> {args}')
            prepared_msg = _process_cmd(cmd, arg_list, Active_cmds)
            if cmd == '$load$' or cmd == '$unload$':
                if 'successful' in prepared_msg.decode() or 'faild' in prepared_msg.decode():
                    active_cmds1 = [cmd[1:-1] for cmd in Active_cmds]
                    print(f'|| active commands = {active_cmds1}')
            conn.sendall(prepared_msg)
            print(f'<< {prepared_msg.decode()}')
    except:

        try:
            conn.sendall(prepared_msg)
            print(f'<< {prepared_msg.decode()}')
        except:
            pass
        finally:
            if client_num == 5:
                pass
            else:
                print('>> $end$')
                print('<< see you again')
            conn.shutdown(SHUT_RDWR)
            print(f'|| connection with client {client_num} terminated')
            print(f'|| socket closed for client {client_num}')
            is_loaded['set1'] = False
            is_loaded['set2'] = False
            is_loaded['set3'] = False
            Active_cmds.clear()
            return




def _reply(conn, out_msg):
    conn.sendall(out_msg)
    return


def _recv_cmd(conn):
    msg=conn.recv(BUFFER).decode()
    cmd , args= _parse_msg(msg)
    cmd_type=_classify_cmd(cmd)
    args=__get_args(conn,cmd_type)
    return cmd,args


def __recv_msg(conn):
    msg = conn.recv(BUFFER)
    conn.sendall(''.encode())
    return msg.decode()


def __get_args(conn, cmd_type, args=None):
    if cmd_type == 'Invalid command':
        return []
    elif cmd_type == 'control':
        conn.sendall('&'.encode())
        in_msg1=conn.recv(BUFFER)
        return [in_msg1.decode()]
    elif cmd_type =='set1':
        conn.sendall('&'.encode())
        in_msg1=conn.recv(BUFFER)
        return [in_msg1.decode()]

    elif cmd_type == 'set2':
        conn.sendall('&'.encode())
        in_msg1 = conn.recv(BUFFER)
        conn.sendall('&'.encode())
        in_msg2 = conn.recv(BUFFER)
        return [in_msg1.decode(), in_msg2.decode()]
    else:
        conn.sendall('&'.encode())
        in_msg1 = conn.recv(BUFFER)
        conn.sendall('&'.encode())
        in_msg2 = conn.recv(BUFFER)
        conn.sendall('&'.encode())
        in_msg3 = conn.recv(BUFFER)
        return [in_msg1.decode(), in_msg2.decode(), in_msg3.decode()]


def _parse_msg(msg):
    msg = msg.split('*')
    new_list = [string for string in msg if string != '']
    if new_list[0].startswith('$') and new_list[0].endswith('$'):
        cmd = new_list[0]
        return cmd, new_list[1:]
    else:
        return None, new_list


def _classify_cmd(cmd):
    classes = {'control': ['end', 'load', 'unload'], 'set1': ['rmvdup', 'flipcase'], 'set2': ['join', 'sub', 'altmerg'],
               'set3': ['substitute']}
    for key, cmd_list in classes.items():
        if cmd[1:-1] in cmd_list:
            return key
    return 'Invalid command'


def _process_cmd(cmd, args, active_cmds):
    out_msg = ''.encode()
    if '$end$' == cmd:
        out_msg = 'see you again'.encode()
    elif '$load$' == cmd:
        if '*set1*' in args:
            if not is_loaded['set1']:
                Active_cmds.append('$rmvdup$')
                Active_cmds.append('$flipcase$')
                out_msg = 'command execution successful'.encode()
                is_loaded['set1'] = True
            else:
                out_msg = 'command execution failed'.encode()

        elif '*set2*' in args:
            if not is_loaded['set2']:
                Active_cmds.append('$sub$')
                Active_cmds.append('$join$')
                Active_cmds.append('$altmerg$')
                out_msg = 'command execution successful'.encode()
                is_loaded['set2'] = True
            else:
                out_msg = 'command execution failed'.encode()

        elif '*set3*' in args:
            if not is_loaded['set3']:
                Active_cmds.append('$substitute$')
                out_msg = 'command execution successful'.encode()
                is_loaded['set3'] = True
            else:
                out_msg = 'command execution failed'.encode()
        else:
            out_msg = 'command execution failed'.encode()

    elif '$unload$' in cmd:

        if '*set1*' in args:
            if is_loaded['set1']:
                Active_cmds.remove('$rmvdup$')
                Active_cmds.remove('$flipcase$')
                out_msg = 'command execution successful'.encode()
                is_loaded['set1'] = False
            else:
                out_msg = 'command execution failed'.encode()

        elif '*set2*' in args:
            if is_loaded['set2']:
                Active_cmds.remove('$join$')
                Active_cmds.remove('$sub$')
                Active_cmds.remove('$altmerg$')
                out_msg = 'command execution successful'.encode()
                is_loaded['set2'] = False
            else:
                out_msg = 'command execution failed'.encode()

        elif '*set3*' in args:
            if is_loaded['set3']:
                Active_cmds.remove('$substitute$')
                out_msg = 'command execution successful'.encode()
                is_loaded['set3'] = False
            else:
                out_msg = 'command execution failed'.encode()
        else:
            out_msg = 'command execution failed'.encode()

    elif '$rmvdup$' == cmd:
        if cmd in Active_cmds:
            out_msg = __process_rmvdup(args).encode()
        else:
            out_msg = 'invalid command'.encode()

    elif '$flipcase$' == cmd:
        if cmd in Active_cmds:
            out_msg = __process_flipcase(args).encode()
        else:
            out_msg = 'invalid command'.encode()

    elif '$join$' == cmd:
        if cmd in Active_cmds:
            out_msg = __process_join(args).encode()
        else:
            out_msg = 'invalid command'.encode()

    elif '$sub$' == cmd:
        if cmd in Active_cmds:
            out_msg = __process_sub(args).encode()
        else:
            out_msg = 'invalid command'.encode()

    elif '$altmerg$' == cmd:
        if cmd in Active_cmds:
            out_msg = __process_altmerg(args).encode()
        else:
            out_msg = 'invalid command'.encode()

    elif '$substitute$' == cmd:
        if cmd in Active_cmds:
            out_msg = __process_substitute(args).encode()
        else:
            out_msg = 'invalid command'.encode()

    else:
        out_msg = 'invalid command'.encode()


    return out_msg


# ------------- Server: Processing of commands -------------------

def __process_load(args, active_cmds):
    # your code here
    return b''


def __process_rmv(args, active_commands):
    # your code here
    return b''


def __process_rmvdup(args):
    args=args[0][1:-1]
    seen = set()
    result = ''
    for char in args:
        if char not in seen:
            seen.add(char)
            result += char
    return result


def __process_flipcase(args):
    args = args[0][1:-1]
    return args.swapcase()


def __process_concat(args):
    # your code here
    return 'GO'


def __process_sub(args):
    arg1 = args[0][1:-1]
    arg2 = args[1][1:-1]
    for char in arg2:
        arg1 = arg1.replace(char, "")
    return arg1


def __process_altmerg(args):
    arg1 = args[0][1:-1]
    arg2 = args[1][1:-1]
    result = ''
    min_length = min(len(arg1), len(arg2))
    for i in range(min_length):
        result += arg1[i] + arg2[i]
    result += arg1[min_length:] + arg2[min_length:]
    return result


def __process_replace(args):
    # your code here
    return 'GO'


# ------------- Your Utility Functions -------------------
def __process_join(args):
    arg1=args[0][1:-1]
    arg2=args[1][1:-1]
    return arg1 + arg2


def __process_substitute(args):
    arg1 = args[0][1:-1]
    arg2 = args[1][1:-1]
    arg3 = args[2][1:-1]
    return arg1.replace(arg2,arg3)