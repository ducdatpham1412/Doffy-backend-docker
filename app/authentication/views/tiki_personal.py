from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK


class TikiPersonal(GenericAPIView):
    def get(self, request):
        res = [
            {
                'id': 1,
                'content': 'Review cho mọi người về cuốn Khởi nghiệp tinh gọn nha',
                'images': 'https://salt.tikicdn.com/cache/w1200/media/catalog/producttmp/ae/e6/07/cb0ebb11383b6b375992ab1f03582fed.jpg',
                'totalLikes': 200,
                'totalComments': 200,
                'creatorId': 1,
                'creatorName': 'Kayly',
                'creatorAvatar': 'https://media.istockphoto.com/photos/portrait-of-happy-vietnamese-young-girl-mekong-river-delta-vietnam-picture-id953601792?b=1&k=20&m=953601792&s=170667a&w=0&h=yRRokWV7uXS9RwKcGENhf-NZQBxh_egHzgD9oBkeoIs=',
                'gender': 0,
                'createdTime': '',
                'color': '',
                'name': 'Sách',
                'numberLikes': 90,
                'numberComments': 20,
                'numberShares': 20,
                'isLiked': 1,
                'relationship': 1
            },
            {
                'id': 2,
                'content': 'Cho mọi người xem chất lượng chiếc iPhone 13 phiên bản US',
                'images': 'https://res-2.cloudinary.com/grover/image/upload/v1649166371/bdk5fczcmjq7xngxarco.png',
                'totalLikes': 90,
                'totalComments': 90,
                'creatorId': 1,
                'creatorName': 'Thomas',
                'creatorAvatar': 'https://icdn.dantri.com.vn/thumb_w/640/2019/12/30/ve-dep-tua-nam-than-cua-hot-boy-17-tuoi-que-bac-lieudocx-1577715096260.jpeg',
                'gender': 0,
                'createdTime': '',
                'color': '',
                'name': 'Công nghệ',
                'numberLikes': 80,
                'numberComments': 10,
                'numberShares': 3,
                'isLiked': 1,
                'relationship': 1
            },
            {
                'id': 3,
                'content': 'Áo croptop hôm qua mới mua từ shop A, nay lên review cho mọi người coi ha',
                'images': 'https://image-us.eva.vn/upload/1-2020/images/2020-02-19/dien-ao-bo-sat-xuong-pho-co-gai-lap-tuc-khien-dan-mang-thuong-nho-boi-mot-chi-tiet-nay-tb2pxc_abywbunksmfpxxxguvxa_15088360-1582125443-94-width600height600.jpg',
                'totalLikes': 80,
                'totalComments': 80,
                'creatorId': 1,
                'creatorName': 'Emma',
                'creatorAvatar': 'https://image-us.eva.vn/upload/1-2020/images/2020-02-19/dien-ao-bo-sat-xuong-pho-co-gai-lap-tuc-khien-dan-mang-thuong-nho-boi-mot-chi-tiet-nay-tb2pxc_abywbunksmfpxxxguvxa_15088360-1582125443-94-width600height600.jpg',
                'gender': 0,
                'createdTime': '',
                'color': '',
                'name': 'Thời trang',
                'numberLikes': 130,
                'numberComments': 20,
                'numberShares': 9,
                'isLiked': 1,
                'relationship': 1
            }
        ]

        return Response(res, HTTP_200_OK)
