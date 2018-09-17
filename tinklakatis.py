import getopt
import threading
import socket
import subprocess
import sys

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print ("""
        \"Tinklakatis\" Net tool
        
        Usage:  tinklakatis.py -t target_host -p port
        -l  --listen                - listen on [host]:[port] for
                                    incoming connections
        -e --execute=file_to_run    - execute the given file upon
                                    recieving a connection
        -c --command                - initialize a command shell
        -u --upload=destination     - upon recieving a connection upload
                                    a file and write to [destination]
        
        
        Examples:
        tinklakatis.py -t 192.168.0.1 -p -l -c
        tinklakatis.py -t 192.168.0.1 -p -l -u=c:\\target.exe
        tinklakatis.py -t 192.168.0.1 -p -l -e="cat /etc/passwd"
        echo 'ABCDEFGHI' | ./tinklakatis.py -t 192.168.0.1 -p 135
        """)
    sys.exit(0)


# main()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connect to your target host
        client.connect((target, port))

        if len(buffer):
            client.send(buffer)

        while True:
            # wait for data back
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print response

            # wait for more input
            buffer = raw_input("")
            buffer += "\n"

            # send it off
            client.send(buffer)

    except:
        print("[*] Exception!!!1111 Exiting")
        client.close()


def server_loop():
    global target

    # if no target is defined, listening on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # thread to handle new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))


def run_command(command):
    # trim the line
    command = command.strip()

    # running the command and geting output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execut command =. \r\n"

    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # check for upload
    if len(upload_destination):
        # read in all bytes bytes and write to our destination
        file_buffer = ""

        # keeep reading data ntil name is available
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # takin the bytes and writing them out
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # acknowledge that file was written
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to safe file to %s\r\n" % upload_destination)

        # check for command excution
        if len(execute):
            # run the command
            output = run_command(execute)
            client_socket.send(output)

        # now we go into another loop if a command shell was requested

        if command:
            while True:
                # show simple promt
                client_socket.send("<Tinklakatis:#> ")
        # now we receive until we see a linefeed
        cmd_buffer = ""
        while "\n" not in cmd_buffer:
            cmd_buffer += client_socket.recv(1024)

        # we have a valid command so execute it and send back the results
        response = run_command(cmd_buffer)

        # send back the response
        client_socket.send(response)


if __name__ == '__main__':
    # global listen
    # global port
    # global execute
    # global command
    # global upload_destination
    # global target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:c:u",
                                   ["help", "listen", "execute", "target", "port", "command", "upload"])

    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "-port"):
            port = int(a)
        else:
            assert False, "Unhandled option"

    # are we going to listen or just send data from stdin?
    if not listen and len(target) and port > 0:
        # read in the buffer from the commandline
        # this will block, so send CTRL-D if not sending input
        # to stdin
        buffer = stdin.read()

        # send data
        client_sender(buffer)

        # we are going to listen and potentially
        # upload things, execute commands, and drop a shell back
        # depending on our command line options above
        if listen:
            server_loop()
