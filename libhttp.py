import socket
import select


class StringBuilder(object):
    """ An helper class used to build string. """
    def __init__(self):
        self._pieces = []
        self._length = 0

    def __str__(self):
        return ''.join(self._pieces)

    def __len__(self):
        return self._length

    @property
    def length(self):
        return self._length

    def append(self, x):
        p = str(x)
        self._length += len(p)
        return self._pieces.append(p)


class HTTPAddress(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, HTTPAddress) and self.host == other.host and self.port == other.port

    @property
    def fullname(self):
        """ Returns 'host:port' """
        return self.host + ':' + str(self.port)

    @property
    def name(self):
        """ Short name of the address in HTTP Host header compliant form.

        For addresses that port is 80, address name is 'host'.
        For addresses that port is not 80, address name is 'host:port'.

        Returns:
            A string representing the address.
        """
        if self.port == 80:
            return self.host
        return self.host + ':' + str(self.port)

    @staticmethod
    def parse(name):
        if not name:
            return None
        host, port = name, 80
        p = name.find(':')
        if p != -1:
            host = name[:p]
            port = int(name[p+1:])
        return HTTPAddress(host, port)


class HTTPStatus:
    """ HTTP status """
    CONTINUE = (100, 'Continue')
    SWITCHING_PROTOCOLS = (101, 'Switching Protocols')
    OK = (200, 'OK')
    CREATED = (201, 'Created')
    ACCEPTED = (202, 'Accepted')
    NON_AUTHORITATIVE_INFORMATION = (203, 'Non-Authoritative Information')
    NO_CONTENT = (204, 'No Content')
    RESET_CONTENT = (205, 'Reset Content')
    MULTIPLE_CHOICES = (300, 'Multiple Choices')
    MOVED_PERMANENTLY = (301, 'Moved Permanently')
    FOUND = (302, 'Found')
    SEE_OTHER = (303, 'See Other')
    USE_PROXY = (305, 'Use Proxy')
    UNUSED = (306, 'Unused')
    TEMPORARY_REDIRECT = (307, 'Temporary Redirect')
    BAD_REQUEST = (400, 'Bad Request')
    PAYMENT_REQUIRED = (402, 'Payment Required')
    FORBIDDEN = (403, 'Forbidden')
    NOT_FOUND = (404, 'Not Found')
    METHOD_NOT_ALLOWED = (405, 'Method Not Allowed')
    NOT_ACCEPTABLE = (406, 'Not Acceptable')
    PROXY_AUTHENTICATION_REQUIRED = (407, 'Proxy Authentication Required')
    REQUEST_TIMEOUT = (408, 'Request Timeout')
    CONFLICT = (409, 'Conflict')
    GONE = (410, 'Gone')
    LENGTH_REQUIRED = (411, 'Length Required')
    PAYLOAD_TOO_LARGE = (413, 'Payload Too Large')
    URI_TOO_LONG = (414, 'URI Too Long')
    UNSUPPORTED_MEDIA_TYPE = (415, 'Unsupported Media Type')
    EXPECTATION_FAILED = (417, 'Expectation Failed')
    UPGRADE_REQUIRED = (426, 'Upgrade Required')
    INTERNAL_SERVER_ERROR = (500, 'Internal Server Error')
    NOT_IMPLEMENTED = (501, 'Not Implemented')
    BAD_GATEWAY = (502, 'Bad Gateway')
    SERVICE_UNAVAILABLE = (503, 'Service Unavailable')
    GATEWAY_TIMEOUT = (504, 'Gateway Timeout')
    HTTP_VERSION_NOT_SUPPORTED = (505, 'HTTP Version Not Supported')

    @staticmethod
    def parse(status_line):
        a = status_line.find(" ")
        a += 1
        while status_line[a] == ' ':
            a += 1
        b = status_line.find(" ", a)
        return HTTPStatus(int(status_line[a:b]))


class HTTPHeaders(object):
    def __init__(self):
        self._items = []

    def __len__(self):
        return len(self._items)

    def __contains__(self, key):
        return self.find(key) != -1

    def __getitem__(self, key):
        val = self.get(key)
        if val is None:
            raise IndexError()
        return val

    def __setitem__(self, key, value):
        return self.set(key, value)

    def items(self):
        return self._items

    @property
    def keys(self):
        for item in self._items:
            yield item[0]

    @property
    def values(self):
        for item in self._items:
            yield item[1]

    def get(self, key, default_value=None):
        key = key.lower()
        for item in self._items:
            if key == item[0].lower():
                return item[1]
        return default_value

    def getall(self, key):
        """ Get all header values associated with the specified key.
        :return: A list of values that are associated with the key
        """
        values = []
        key = key.lower()
        for item in self._items:
            if key == item[0].lower():
                values.append(item[1])
        return values

    def set(self, key, value):
        i = self.find(key)
        if i != -1:
            self._items[i] = (key, value)
        self.append((key, value))

    def setall(self, key, value):
        i = self.find(key)
        if i != -1:
            self._items[i] = (key, value)
            # remove other values
            self.remove(key, i + 1)
        else:
            self.append((key, value))

    def find(self, key, start=0):
        key = key.lower()
        for i in range(start, len(self._items)):
            if key == self._items[i][0].lower():
                return i
        return -1

    def append(self, kv):
        self._items.append((str(kv[0]), str(kv[1])))

    def remove(self, key, start=0):
        """ Removes the first header matching the key starting from start """
        i = self.find(key, start)
        if i != -1:
            self._items.pop(i)

    def removeall(self, key, start=0):
        """ Removes all headers matching the key starting from start """
        i = self.find(key, start)
        while i != -1:
            self._items.pop(i)
            i = self.find(key, i)

    def pop(self, i):
        """ Removes the i-th header. """
        self._items.pop(i)

    def at(self, i):
        """ Gets the i-th header. Returns 2-tuple (key, value) """
        return self._items[i]


class HTTPMessage(object):
    def __init__(self):
        self.headers = HTTPHeaders()
        self.body = ""
        self.body_pending = False

    def __str__(self):
        s = StringBuilder()
        s.append(self.start + "\r\n")
        for k, v in self.headers.items():
            s.append(k + ": " + v + "\r\n")
        s.append("\r\n")
        if self.body:
            s.append(self.body)
        return str(s)

    def __contains__(self, item):
        return self.headers.__contains__(item)

    def __getitem__(self, item):
        return self.headers.__getitem__(item)

    def __setitem__(self, key, value):
        return self.headers.__setitem__(key, value)

    @property
    def start(self):
        """ start line getter """
        return ''

    @start.setter
    def start(self, start_line):
        """ start line setter """
        pass

    def add(self, kv):
        """ Adds a header.
        :param  kv -> (key, value)
        """
        self.headers.append(kv)

    def set(self, kv):
        self.headers.set(kv[0], kv[1])

    def remove(self, key):
        self.headers.remove(key)

    def append(self, data):
        """ Append data to message body. """
        self.body += data

    def get(self, key, default_value=None):
        """ Get the value associated with the key. """
        return self.headers.get(key, default_value)

    def get_int(self, key, default_value=0):
        """ Get the integer value associated with the key. """
        val = self.headers.get(key)
        if val is not None:
            return int(val)
        return default_value

    def get_float(self, key, default_value=0.0):
        """ Get the float value associated with the key. """
        val = self.headers.get(key)
        if val is not None:
            return float(val)
        return default_value


class HTTPRequest(HTTPMessage):
    def __init__(self, method='GET', target='/', version='HTTP/1.1'):
        self.method = method
        self.target = target
        self.version = version
        HTTPMessage.__init__(self)

    @property
    def start(self):
        return self.method + ' ' + self.target + ' ' + self.version

    @start.setter
    def start(self, start_line):
        a = start_line.find(" ")
        b = start_line.rfind(" ")
        self.method = start_line[:a].strip(" \t")
        self.target = start_line[a + 1:b].strip(" \t")
        self.version = start_line[b+1:].strip(" \t")
        if not self.method or not self.target or not self.version:
            raise ValueError("Bad HTTP request line: " + start_line)

    @property
    def request(self):
        return self.method, self.target, self.version

    @request.setter
    def request(self, r):
        self.method = r[0]
        self.target = r[1]
        self.version = r[2]


class HTTPResponse(HTTPMessage):
    def __init__(self, status=HTTPStatus.OK, version='HTTP/1.1'):
        self.version = version
        self.code = status[0]
        self.phrase = status[1]
        HTTPMessage.__init__(self)

    def status_is(self, status):
        """ Test status code. """
        return self.code == status[0]

    @property
    def start(self):
        return self.version + ' ' + str(self.code) + ' ' + self.phrase

    @start.setter
    def start(self, start_line):
        a = start_line.find(' ')
        self.version = start_line[:a]
        a += 1
        while start_line[a] == ' ':
            a += 1
        b = start_line.find(' ', a)
        self.code = int(start_line[a:b])
        self.phrase = start_line[b:].strip(" \t")

    @property
    def response(self):
        return self.version, self.code, self.phrase

    @response.setter
    def response(self, r):
        self.version = r[0]
        self.code = r[1]
        self.phrase = r[2]


class HTTPInputStream(object):
    """ An HTTPInputStream represents an inbound HTTP octet stream. """
    BUFFER_LIMIT = 128 * 1024

    def __init__(self, conn=None):
        self._conn = conn              # socket connection
        self._bytes_in = 0
        self._rdbuf = ""               # read buffer

    @property
    def rdbuf(self):
        """ Gets the read buffer """
        return self._rdbuf

    @property
    def bytes_in(self):
        """ Total number of bytes read from the socket """
        return self._bytes_in

    def wait(self):
        """ Wait till the underlying socket object is ready for reading.

        This method returns immediately if the read buffer is not empty.

        Returns:
            Number of bytes available for reading, which may be 0 if the read buffer
        is empty and the connection has been closed.
        """
        if not self._rdbuf:
            try:
                self._rdbuf = self._conn.recv(HTTPInputStream.BUFFER_LIMIT)
                self._bytes_in += len(self._rdbuf)
            except Exception, e:
                raise IOError(str(e))
        return len(self._rdbuf)

    def read_some(self, max_count):
        """ Read up to max_count bytes from the stream.

        Args:
            max_count: Maximum number of bytes to read

        Returns:
            Up to max_count bytes data read from the stream.
        """
        if not self.wait():
            return ""
        r = self._rdbuf[:max_count]
        self._rdbuf = self._rdbuf[max_count:]
        return r

    def read(self, n):
        """ Read exactly n bytes from the stream.

        Args:
            n: Number of bytes to read

        Returns:
            A string contains the data read, of which the length will be exactly n.

        Raises:
            IOError: An error occurred reading the underlying socket.
            EOFError: EOF was encountered before read complete.
        """
        r = StringBuilder()
        while len(r) < n:
            if not self.wait():
                raise EOFError("Connection closed unexpectedly.")

            a = n - r.length
            if a < len(self._rdbuf):
                a = len(self._rdbuf)
            r.append(self._rdbuf[:a])
            self._rdbuf = self._rdbuf[a:]
        return str(r)

    def read_line(self):
        """ Extracts characters from the stream till a CRLF is encountered.

        The CRLF is extracted but discarded.

        Returns:
            A string contains characters extracted excluding the trailing CRLF.

        Raises:
            IOError: An error occurred reading the underlying socket.
            EOFError: EOF was encountered before read complete.
        """
        r = StringBuilder()
        crlf_pos = -1
        while crlf_pos == -1:
            if len(r) >= HTTPInputStream.BUFFER_LIMIT:
                raise IOError("HTTPInputStream.read_line too long")

            if not self.wait():
                raise EOFError("HTTPInputStream.read_line EOF")

            crlf_pos = self._rdbuf.find("\r\n")
            if crlf_pos != -1:
                r.append(self._rdbuf[:crlf_pos])
                self._rdbuf = self._rdbuf[crlf_pos + 2:]
            else:
                r.append(self._rdbuf)
                self._rdbuf = ""
        return str(r)

    def read_chunk(self):
        """ Extracts a chunk from the stream.

        A chunk consists of a chunk-size header and a chunk-body:
            CHUNK = CHUNK-SIZE CRLF
                    CHUNK-BODY CRLF
        This method reads the whole chunk and returns chunk-body. The chunk-size is
        implied by the length of returned data.

        Returns:
            Chunk-body, a string object.

        Raises:
            IOError: An error occurred reading the underlying socket or something is wrong with
                the chunk format.
            EOFError: EOF was encountered before read complete.
        """
        chunk_size = int(self.read_line())
        d = self.read(chunk_size)
        if self.read(2) != "\r\n":
            raise IOError("Corrupted chunk stream: inconsistent chunk size.")
        return d

    def read_message(self, m):
        """ Extracts an HTTP message from the stream.

        Note that the message body will be extracted only when Content-Length header is present and
        its value is no larger than BUFFER_LIMIT. Otherwise, the message body will not be extracted
        and body_pending flag of the extracted message will be set, regardless of whether message
        body is missing or not.

        If the body_pending flag of the returned message is set, it simply means that the message
         body is not processed.

        Raises:
            IOError: An error occurred reading the underlying socket.
            EOFError: EOF was encountered before read complete.
        """
        m.start = self.read_line()
        prev_line = ""
        curr_line = self.read_line()
        while len(curr_line):
            if curr_line[0] in " \t":
                # folded header field value
                prev_line += curr_line.strip(" \t")
            else:
                if len(prev_line):
                    m.add(self._split_header(prev_line))
                prev_line = curr_line
            curr_line = self.read_line()

        if len(prev_line):
            m.add(self._split_header(prev_line))

        # Read message body only when the size of body is explicitly told
        # and the size of message body is under buffer size limit
        m.body = ""
        body_size = m.get_int("Content-Length", -1)
        if 0 <= body_size <= HTTPInputStream.BUFFER_LIMIT:
            m.body = self.read(body_size)
            m.body_pending = False
        else:
            # To be determined
            m.body_pending = True
        return m

    def read_request(self):
        """ Extracts an HTTP request message from the input stream.

        See docstring of read_message method for more information.

        Returns:
            An HTTPRequest object.
        """
        r = HTTPRequest()
        self.read_message(r)
        if r.method in ["GET", "HEAD", "DELETE", "CONNECT", "TRACE"]:
            # Requests with those methods may not carry a payload
            r.body_pending = False
        # POST, PUT, OPTIONS
        return r

    def read_response(self):
        """ Extracts an HTTP response message from the input stream.

        See docstring of read_message method for more information.

        Returns:
            An HTTPResponse object.
        """
        r = HTTPResponse()
        self.read_message(r)
        return r

    def close(self):
        """  Close the HTTP input stream. """
        self._conn.shutdown(socket.SHUT_RD)

    @staticmethod
    def _split_header(line):
        p = line.find(":")
        return line[:p].strip(" \t"), line[p + 1:].strip(" \t")


class HTTPOutputStream(object):
    """ An HTTPInputStream represents an outbound HTTP octet stream. """
    def __init__(self, conn):
        self._conn = conn
        self._bytes_out = 0

    @property
    def bytes_out(self):
        """ Total number of bytes written to the socket. """
        return self._bytes_out

    def write_some(self, data):
        """ Writes data into the output stream.

        It's possible that only part of data is written.

        Returns:
            Number of bytes written, which may be less then len(data).

        Raises:
            IOError: An error occurred writing the underlying socket.
        """
        n = self._conn.send(data)
        if n > 0:
            self._bytes_out += n
        return n

    def write(self, data):
        """ Writes data into the output stream.

        Returns:
            Number of bytes written, which is exactly len(data).

        Raises:
            IOError: An error occurred writing the underlying socket.
        """
        written = 0
        while written != len(data):
            count = self.write_some(data[written:])
            if count <= 0:
                raise IOError("HTTPOutputStream.write error: Connection closed before write complete.")
            written += count
        return len(data)

    def write_line(self, data):
        """ Writes data with a CRLF appended.

        Returns:
            Number of bytes written.
        """
        return self.write(data) + self.write("\r\n")

    def write_chunk(self, data):
        """ Writes data in "chunked" transfer encoding.

        This method writes "len(data) CRLF data CRLF" into the stream.

        Returns:
            Number of bytes written.
        """
        return self.write_line(str(len(data))) + self.write_line(data)

    def write_message(self, m):
        """ Writes an HTTP message into the output stream.

        Returns:
            Number of bytes written.

        Raises:
            IOError: An error occurred writing the underlying socket.
        """
        return self.write(str(m))

    def copy_bytes(self, src, count):
        """ Copy count bytes from src to the output stream.

        Args:
            src: An HTTPInputStream object.
            count: Number of bytes to copy.

        Returns:
            Number of bytes copied.
        """
        copied = 0
        while copied < count:
            d = src.read_some(count-copied)
            if not d:
                raise EOFError("HTTPOutputStream.copy_bytes EOF count=" + str(count-copied))
            self.write(d)
            copied += len(d)
        return count

    def copy_chunks(self, src):
        """ Copy chunks from src to the output stream.

        This method will not return until an empty chunk is encountered and copied.
        See RFC7320 Section 4.1 for more information about HTTP "chunked" transfer encoding.

        Returns:
            Number of bytes copied.
        """
        count = 0
        while True:
            chunk_header = src.read_line()
            chunk_size = int(chunk_header.strip(" \t").split(' ', 1)[0], 16)
            if chunk_size <= 0:
                # end of chunks
                break

            self.write(chunk_header + "\r\n")
            self.copy_bytes(src, chunk_size + 2)
            count += len(chunk_header) + chunk_size + 4

        self.write("0\r\n")
        count += 2
        return count

    def copy_lines(self, src):
        """ Copy lines from src to the output stream.

        This method will not return until an empty is encountered and copied.

        Args:
            src: An HTTPInputStream object.

        Returns:
            Number of bytes copied.
        """
        count = 0
        trailer_line = src.read_line()
        while len(trailer_line):
            self.write(trailer_line + "\r\n")
            count += len(trailer_line) + 2
            trailer_line = src.read_line()
        self.write("\r\n")
        count += 2
        return count

    def copy_all(self, src):
        """ Copy all data from src to the output stream.

        This method will not return until src is closed and all data from src has
        been written to the output stream.

        Args:
            src: An HTTPInputStream object.

        Returns:
            Number of bytes copied.
        """
        d = src.read_some()
        while d:
            self.write(d)
            d = src.read_some()

    def close(self):
        self._conn.shutdown(socket.SHUT_WR)


class HTTPIOStream(HTTPInputStream, HTTPOutputStream):
    def __init__(self, conn=None, addr=None):
        if addr is None and conn is not None:
            name = conn.getpeername()
            addr = HTTPAddress(name[0], name[1])
        elif conn is None and addr is not None:
            if isinstance(addr, tuple):
                conn = socket.create_connection(addr)
            elif isinstance(addr, HTTPAddress):
                conn = socket.create_connection((addr.host, addr.port))
        HTTPInputStream.__init__(self, conn)
        HTTPOutputStream.__init__(self, conn)
        self._address = addr

    def is_open(self):
        return self._conn is not None

    def __nonzero__(self):
        return self.is_open()

    @property
    def socket(self):
        return self._conn

    @property
    def name(self):
        return str(self.address)

    @property
    def address(self):
        """ HTTPAddress of peer """
        return self._address

    def open(self, addr):
        self.close()
        if isinstance(addr, tuple):
            conn = socket.create_connection(addr)
        elif isinstance(addr, HTTPAddress):
            conn = socket.create_connection((addr.host, addr.port))
        self._conn = conn
        self._address = addr

    def close(self):
        if self._conn:
            try:
                self._conn.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self._conn.close()
            except:
                pass
            self._conn = None
        self._address = None


class HTTPTunnel:
    def __init__(self, peers):
        self.peers = peers

    def _getpair(self, rdsock):
        if rdsock == self.peers[0].socket:
            return self.peers[0], self.peers[1]
        return self.peers[1], self.peers[0]

    def run(self):
        """ Do blind forward till either of the peer connections is closed or an error occurs. """
        if self.peers[0].rdbuf:
            self.peers[1].write(self.peers[0].rdbuf)
        if self.peers[1].rdbuf:
            self.peers[0].write(self.peers[1].rdbuf)
        watch = [self.peers[0].socket, self.peers[1].socket]
        while watch:
            r, w, x = select.select(watch, [], [])
            for u in r:
                src, dst = self._getpair(u)
                d = src.read_some(16*1024)
                if not d:
                    # connection closed
                    watch.remove(u)
                else:
                    dst.write(d)

