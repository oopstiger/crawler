# The following code is auto generated by jpc.py
# Source JSON file: qunar\hotel_review_content.json
class hotel_review_content(object):
    def __init__(self):
        self.from_ = u''
        self.isOrderBind = False
        self.fileTypes = []
        self.title = u''
        self.feedContentStatus = 0
        self.hotelUrl = u''
        self.imageUrl = []
        self.subScores = []
        self.detailUrl = u''
        self.checkInDate = u''
        self.hotelName = u''
        self.objSeq = u''
        self.version = 0
        self.fileStatus = []
        self.recommend = u''
        self.feedContent = u''
        self.tripType = u''
        self.evaluationDesc = u''
        self.evaluation = 0
        self.extUrl = u''
    
    @staticmethod
    def from_dict(dct):
        if not dct:
            return None
        obj = hotel_review_content()
        obj.from_ = dct.get("from")
        obj.isOrderBind = dct.get("isOrderBind")
        obj.fileTypes = dct.get("fileTypes")
        obj.title = dct.get("title")
        obj.feedContentStatus = dct.get("feedContentStatus")
        obj.hotelUrl = dct.get("hotelUrl")
        obj.imageUrl = dct.get("imageUrl")
        obj.subScores = hotel_review_content_subScores_from_list(dct.get("subScores"))
        obj.detailUrl = dct.get("detailUrl")
        obj.checkInDate = dct.get("checkInDate")
        obj.hotelName = dct.get("hotelName")
        obj.objSeq = dct.get("objSeq")
        obj.version = dct.get("version")
        obj.fileStatus = dct.get("fileStatus")
        obj.recommend = dct.get("recommend")
        obj.feedContent = dct.get("feedContent")
        obj.tripType = dct.get("tripType")
        obj.evaluationDesc = dct.get("evaluationDesc")
        obj.evaluation = dct.get("evaluation")
        obj.extUrl = dct.get("extUrl")
        return obj


class hotel_review_content_subScores_item(object):
    def __init__(self):
        self.tag = u''
        self.score = 0
        self.desc = u''
    
    @staticmethod
    def from_dict(dct):
        if not dct:
            return None
        obj = hotel_review_content_subScores_item()
        obj.tag = dct.get("tag")
        obj.score = dct.get("score")
        obj.desc = dct.get("desc")
        return obj


def hotel_review_content_subScores_from_list(lst):
    if not lst:
        return None
    values = []
    for v in lst:
        values.append(hotel_review_content_subScores_item.from_dict(v))
    return values
