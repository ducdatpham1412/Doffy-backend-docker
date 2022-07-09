from rest_framework.generics import GenericAPIView
from rest_framework.status import HTTP_200_OK
from rest_framework.response import Response


class TikiCampaign(GenericAPIView):
    def get(self, request):
        res = [
            {
                'id': 0,
                'content': 'Shop mở bán 100 cuốn sách Nguyễn Nhật Ánh cho 100 bạn mua chung với giá chỉ 10k',
                'images': 'https://www.nxbtre.com.vn/Images/Book/nxbtre_full_01372019_043734.jpg',
                'chatTagId': 0,
                'creatorId': 1,
                'createdTime': '',
                'color': 0,
                'name': 'Sách',
                'relationship': 1
            },
            {
                'id': 0,
                'content': 'Chia sẻ kinh nghiệm phối đồ đi biển cho mùa hè',
                'images': 'https://image-us.24h.com.vn/upload/1-2019/images/2019-03-13/1552412352-449-6-kieu-thoi-trang-di-bien-que-mot-cuc-nay-da-bi-thay-the-3-1531819390-width500height632.jpg',
                'chatTagId': 0,
                'creatorId': 1,
                'createdTime': '',
                'color': 0,
                'name': 'Du lịch - Thời trang',
                'relationship': 1
            },
        ]

        return Response(res, HTTP_200_OK)
