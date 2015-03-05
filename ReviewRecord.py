import md5


class ReviewRecord(object):
    def __init__(self):
        self.hotel_name = ""
        self.hotel_url = ""
        self.source_site = ""
        self.rate = 3
        self.nick_name = ""
        self.comment = ""
        self.comment_date = ""
        self.check_in_date = ""
        self.timestamp = ""
        self.consume_detail = ""

    @property
    def hash(self):
        h = md5.new()
        text = []
        if self.nick_name:
            text.append(self.nick_name.encode('utf-8'))
        if self.hotel_name:
            text.append(self.hotel_name.encode('utf-8'))
        if self.source_site:
            text.append(self.source_site.encode('utf-8'))
        if self.comment:
            text.append(self.comment.encode('utf-8'))
        if self.check_in_date:
            text.append(self.check_in_date.encode('utf-8'))
        text.append(str(self.rate))
        h.update('-'.join(text))
        return h.hexdigest()
