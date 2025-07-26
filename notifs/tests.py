# notifs/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from notifs.models import Notification, Activity
from social.models import UserFollows

User = get_user_model()


class FollowSignalTest(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="a")
        self.b = User.objects.create_user(username="b")

    @patch("notifs.utils.send_expo_push")  # 푸시 실제 호출 막기
    def test_follow_creates_notification(self, mock_push):
        UserFollows.objects.create(follower=self.a, following=self.b)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Activity.objects.count(), 1)

        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.b)
        self.assertEqual(notif.actor, self.a)
        mock_push.assert_called_once()
