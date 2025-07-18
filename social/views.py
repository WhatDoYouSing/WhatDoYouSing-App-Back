from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User
from social.models import UserFollows
from django.db.models import Q
from rest_framework import status
from django.shortcuts import get_object_or_404

class FollowerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 나를 팔로우하는 사람들
        followers = UserFollows.objects.filter(following=user).values_list("follower", flat=True)

        # 내가 팔로우한 사람들 (following 리스트)
        my_following_ids = UserFollows.objects.filter(follower=user).values_list("following", flat=True)

        # 유저 객체 리스트
        follower_users = User.objects.filter(id__in=followers)

        result = []
        for follower in follower_users:
            result.append({
                "id": follower.id,
                "title": follower.title,
                "serviceID": follower.serviceID,
                "nickname": follower.nickname,
                "profile": follower.profile,
                "following": follower.id in my_following_ids  # 내가 그 사람을 팔로우하는지 여부
            })

        return Response({
            "message": "팔로워 목록 조회 성공",
            "data":{
                "my_nickname": user.nickname,
                "followers": result
            }
        }, status=200)
    
class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 내가 팔로우한 유저들
        followings = UserFollows.objects.filter(follower=user).select_related('following')
        following_users = [f.following for f in followings]

        # 나를 팔로우하고 있는 유저들 (for 상호팔로우 체크)
        followers = set(
            UserFollows.objects.filter(following=user).values_list("follower_id", flat=True)
        )

        result = []
        for following in following_users:
            result.append({
                "id": following.id,
                "title": following.title,
                "serviceID": following.serviceID,
                "nickname": following.nickname,
                "profile": following.profile,
                "following": following.id in followers  # 상대가 나를 팔로우하고 있으면 true
            })

        return Response({
            "message": "팔로잉 목록 조회 성공",
            "data": {
                "my_nickname": user.nickname,
                "followings": result
            }
        }, status=status.HTTP_200_OK)
    

class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = request.user
        target_user = get_object_or_404(User, id=user_id)

        if user == target_user:
            return Response({"error": "자기 자신을 팔로우할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        follow_obj = UserFollows.objects.filter(follower=user, following=target_user).first()

        if follow_obj:
            follow_obj.delete()
            return Response({"message": f"{target_user.nickname}님 팔로우를 취소했습니다."}, status=status.HTTP_200_OK)
        else:
            UserFollows.objects.create(follower=user, following=target_user)
            return Response({"message": f"{target_user.nickname}님을 팔로우했습니다."}, status=status.HTTP_201_CREATED)
