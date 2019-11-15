"""
 Implements a simple HTTP/1.0 Server

"""
import datetime
import socket
import threading
import logging
import json
import db
import time

# Define socket host and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)


# ----------------- Dictionaries -----------------

mimetypes_dict = {
    0: 'text/html',
    1: 'text/css',
    2: 'image/jpg',
    3: 'image/png',
    4: 'image/gif',
    5: 'image/x-icon',
    6: 'image/svg',
    7: 'image/webp',
    8: 'audio/mpeg',
    9: 'audio/ogg',
    10: 'video/mp4',
    11: 'video/ogg',
    12: 'application/pdf',
    13: 'application/json',
}

form_dict = {
    'firstname: ': '',
    'lastname: ': ''}


# --------------------------------- Select mimetype ---------------------------------

def select_mimetype(request_filename):

    # Check file extension of file
    mimetype = ''
    if request_filename.endswith('/'):
        mimetype = mimetypes_dict.get(0)
    if request_filename.endswith('.html'):
        mimetype = mimetypes_dict.get(0)
    if request_filename.endswith('.css'):
        mimetype = mimetypes_dict.get(1)
    if request_filename.endswith('.jpg'):
        mimetype = mimetypes_dict.get(2)
    if request_filename.endswith('.png'):
        mimetype = mimetypes_dict.get(3)
    if request_filename.endswith('.gif'):
        mimetype = mimetypes_dict.get(4)
    if request_filename.endswith('.ico'):
        mimetype = mimetypes_dict.get(5)
    if request_filename.endswith('.svg'):
        mimetype = mimetypes_dict.get(6)
    if request_filename.endswith('.webp'):
        mimetype = mimetypes_dict.get(7)
    if request_filename.endswith('.mp3'):
        mimetype = mimetypes_dict.get(8)
    if request_filename.endswith('.ogg'):
        mimetype = mimetypes_dict.get(9)
    if request_filename.endswith('.mp4'):
        mimetype = mimetypes_dict.get(10)
    if request_filename.endswith('.ogv'):
        mimetype = mimetypes_dict.get(11)
    if request_filename.endswith('.pdf'):
        mimetype = mimetypes_dict.get(12)
    if request_filename.endswith('/form'):
        mimetype = mimetypes_dict.get(13)

    return mimetype


# --------------------------------- Handle Client ---------------------------------

def handle_client(connection, address):
    while True:
        try:
            request = connection.recv(1024).decode()
            if request != '':
                connection_close, response = handle_request(request, address[0])
                connection.sendall(response)
                if connection_close:
                    break
        except (ConnectionAbortedError, socket.timeout):
            break

    print("Client connection closed")
    connection.close()


# --------------------------------- Handle Request ---------------------------------

def handle_request(request, address):

    # Parse headers
    headers = request.split('\n')
    get_content = headers[0].split()
    print(get_content)

    request_method = get_content[0]
    request_filename = get_content[1]

    # Close connenction
    connection_close = headers[6].split()[1] == 'close'

    # Request methods
    if request_method == 'GET':
        response = do_GET(request, address, request_filename)
    elif request_method == 'HEAD':
        response = do_HEAD(request)
    elif request_method == 'POST':
        response = do_POST(request, address, request_filename)
    elif request_method == 'PUT':
        response = do_PUT(request, address, request_filename)
    elif request_method == 'DELETE':
        response = do_DELETE(request, address, request_filename)
    else:
        response = 'Method Not Allowed'.encode('utf-8')
        headers = response_headers('405', 'text/html', len(response), 'GET, HEAD, POST, PUT, DELETE')
        final_response = headers + response
        return final_response

    return connection_close, response


# --------------------------------- Handle Request do_GET ---------------------------------

def do_GET(request, address, request_filename):

    # Set mimetype
    mimetype = select_mimetype(request_filename)

    # Load index.html as default
    if request_filename == '/':
        request_filename = '/index.html'

    # Get file
    response = get_file(request_filename, mimetype)

    # Private page
    if request_filename.endswith('/private/file.html'):
        if user_is_authenticated(address) is False:
            response = 'You have not permission to acess this page! Please login or register. ' \
                       '<a href="/public/authentication.html">Login/Register</a>'.encode('utf-8')
            headers = response_headers('403', mimetype, len(response))
            final_response = headers + response
            return final_response
    elif request_filename.endswith('/logout'):
        logout(address)
        response = '<html><body>Successful logout! <a href="/">Home page</a></body></html>'.encode('utf-8')
        headers = response_headers('200', mimetype, len(response))
        final_response = headers + response
        return final_response
    elif request_filename.endswith('/delete'):
        response = '<html><body> Account successfuly deleted! ' \
                   '<a href="/">Home page</a></body></html>'.encode('utf-8')
        headers = response_headers('200', mimetype, len(response))
        final_response = headers + response
        return final_response
    elif request_filename.endswith('/update'):
        response = '<html><body> Successful update! <a href="/">Home page</a></body></html>'.encode('utf-8')
        headers = response_headers('200', 'text/html', len(response))
        final_response = headers + response
        return final_response
    elif request_filename.endswith('/delete'):
        response = '<html><body>Account deleted! ' \
                   '<a href="/">Home page</a></body></html>'.encode('utf-8')
        headers = response_headers('200', mimetype, len(response))
        final_response = headers + response
        return final_response

    # Generate log file
    if request_filename.endswith('.html'):
        logging.basicConfig(format='[%(asctime)s] - %(message)s', datefmt='%d/%m/%Y %H:%M:%S',
                            filename='log.txt',
                            # filemode='w',
                            level=logging.DEBUG)
        logging.info('%s - http://localhost:8000%s ', client_address, request_filename)

    return response


# --------------------------------- Handle Request do_HEAD ---------------------------------

def do_HEAD(request):
    headers = request.split('\n')
    get_content_type = headers[1]
    mimetype = get_content_type.split(':')[1]
    headers = response_headers('200', mimetype, 0)
    return headers


# --------------------------------- Handle Request do_POST ---------------------------------

def do_POST(request, address, request_filename):
    # Set mimetype
    mimetype = select_mimetype(request_filename)

    # Get form data
    headers = request.split('\n')
    get_content = headers[-1]
    form_data1 = get_content.split('&')[0].split('=')[1]
    form_data2 = get_content.split('&')[1].split('=')[1]

    if request_filename.endswith('/form'):
        form_dict['firstname: '] = form_data1
        form_dict['lastname: '] = form_data2
        response = json.dumps(form_dict).encode('utf-8')
        headers = response_headers('200', 'application/json', len(response))
        final_response = headers + response
        return final_response
    elif request_filename.endswith('/register'):
        registration = register(address, form_data1, form_data2)
        if registration is True:
            response = '<html><body> Successful registration! ' \
                       '<a href="/public/authentication.html">Login</a></body></html>'.encode('utf-8')
            headers = response_headers('200', mimetype, len(response))
            final_response = headers + response
            return final_response
        else:
            response = '<html><body> Registration failed! ' \
                       '<a href="/public/authentication.html">Register</a></body></html>'.encode('utf-8')
            headers = response_headers('200', mimetype, len(response))
            final_response = headers + response
            return final_response
    elif request_filename.endswith('/login'):
        logging_in = login(address, form_data1, form_data2)
        if logging_in is True:
            response = '<html><body> Successful login! <a href="/">Home page</a> </body></html>'.encode('utf-8')
            headers = response_headers('200', mimetype, len(response))
            final_response = headers + response
            return final_response
        else:
            response = '<html><body> Invalid login! ' \
                       '<a href="/public/authentication.html">Login</a></body></html>'.encode('utf-8')
            headers = response_headers('403', mimetype, len(response))
            final_response = headers + response
            return final_response


# --------------------------------- Handle Request do_PUT ---------------------------------

def do_PUT(request, address, request_filename):

    # Get json data
    username = request.split('\n')[-1].split(':')[1].split('"')[1]
    password = request.split('\n')[-1].split(':')[2].split('"')[1]

    update = update_user(username, password, address)

    if request_filename.endswith('/update'):
        if update is True:
            response = '<html><body> Successful update! <a href="/">Home page</a></body></html>'.encode('utf-8')
            headers = response_headers('200', 'text/html', len(response))
            final_response = headers + response
            return final_response
        else:
            response = '<html><body>Error updating! ' \
                       '<a href="/public/update.html">Go back</a></body></html>'.encode('utf-8')
            headers = response_headers('200', 'text/html', len(response))
            final_response = headers + response
            return final_response


# --------------------------------- Handle Request do_DELETE ---------------------------------

def do_DELETE(request, address, request_filename):
    # Set mimetype
    mimetype = select_mimetype(request_filename)

    user = db.get_user_logged_in_credentials(address)
    username = user['username']
    password = user['password']

    logout(address)
    db.delete_user(address, username, password)
    if request_filename.startswith('/delete'):
        response = '<html><body> Account successfuly deleted! ' \
                   '<a href="/">Home page</a></body></html>'.encode('utf-8')
        headers = response_headers('200', mimetype, len(response))
        final_response = headers + response
        return final_response
    else:
        response = '<html><body>Error deleting your account! ' \
                   '<a href="/private/file.html">Go back</a></body></html>'.encode('utf-8')
        headers = response_headers('200', mimetype, len(response))
        final_response = headers + response
        return final_response


# --------------------------------- Authentication ---------------------------------

def register(address, username, password):
    if username is '' or password is '':
        return False
    else:
        db.add_user(address, username, password)
        return True


def login(address, username, password):
    user = db.get_user_login(username, password)
    if user is not None:
        db.update_user_logged_in_status(1, address, username, password)
        return True


def user_is_authenticated(address):
    user = db.get_user_status(address)
    if user is not None:
        user_status = user['user_logged_in']
        if user_status == 1:
            return True  # authenticated
        else:
            return False  # not authenticated
    return False


def logout(address):
    user_logged_in = db.get_user_logged_in_credentials(address)
    username = user_logged_in['username']
    password = user_logged_in['password']
    return db.update_user_logged_in_status(0, address, username, password)


def update_user(username, password, address):
    if username is '' or password is '':
        return False
    else:
        db.update_user(username, password, address)
        return True


# --------------------------------- Response headers---------------------------------

def response_headers(status_code, content_type, content_length, allow=None):
    header = ''
    # Status codes
    if status_code == '200':
        header += 'HTTP/1.1 200 OK\n'
    elif status_code == '400':
        header += 'HTTP/1.1 400 BAD REQUEST\n'
    elif status_code == '307':
        header += 'HTTP/1.1 307 TEMPORARY REDIRECT\n'
    elif status_code == '403':
        header += 'HTTP/1.1 403 FORBIDDEN\n'
    elif status_code == '404':
        header += 'HTTP/1.1 404 NOT FOUND\n'
    elif status_code == '405':
        header += 'HTTP/1.1 405 METHOD NOT ALLOWED\n'

    if allow is not None:
        header += 'Allow: %s' % allow + '\n'
    header += 'Content-Type: %s' % content_type + '\n'
    header += 'Content-Length: %s' % content_length + '\n'
    header += 'Date: %s' % str(datetime.datetime.now()) + '\n'
    header += 'Cache-Control: no-cache\n'
    header += 'Server: httpserver\n\n'

    end_header = header.encode('utf-8')
    return end_header


# --------------------------------- Cache ---------------------------------


def get_file(request_filename, mimetype):
    n = 2
    top2 = db.get_top2_url(n)
    file_from_cache = get_file_from_cache(request_filename, mimetype)
    file_from_server = get_file_from_server(request_filename, mimetype)
    if file_from_cache is not None:
        if request_filename not in top2[0]['url'] and request_filename not in top2[1]['url']:
            # print('Fetching from server just because not top2. ')
            increment_requests(request_filename)
            time.sleep(0.1)
            return file_from_server
        else:
            # print("Fetching from cache. ")
            increment_requests(request_filename)
            return file_from_cache
    else:
        # print('Fetching from server.')
        save_file_in_cache(request_filename)
        return file_from_server


def increment_requests(request_filename):
    requests = db.get_requests_url(request_filename)
    count = requests['requests']
    count += 1
    db.set_requests_url(count, request_filename)


def get_file_from_cache(request_filename, mimetype):
    data = db.get_url_in_cache(request_filename)
    if data:
        filename = data['url']
        try:
            fin = open('htdocs' + filename, 'rb')
            response = fin.read()
            fin.close()
            headers = response_headers('200', mimetype, len(response))
            final_response = headers + response
            return final_response
        except Exception as ex:
            response = 'File Not Found'.encode('utf-8')
            headers = response_headers('404', mimetype, len(response))
            final_response = headers + response
            return final_response

    else:
        return None


def get_file_from_server(request_filename, mimetype):
    try:
        # Read file contents
        fin = open('htdocs/' + request_filename, 'rb')
        response = fin.read()
        fin.close()
        headers = response_headers('200', mimetype, len(response))
        final_response = headers + response
        return final_response
    except Exception as ex:
        response = 'File Not Found'.encode('utf-8')
        headers = response_headers('404', mimetype, len(response))
        final_response = headers + response
        return final_response


def save_file_in_cache(request_filename):
    save_file = db.save_file(request_filename)
    return save_file


# create db
# db.create_db()

while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    client_connection.settimeout(10)

    # Thread
    thread = threading.Thread(target=handle_client, args=(client_connection, client_address,))
    thread.start()

# Close socket
server_socket.close()
