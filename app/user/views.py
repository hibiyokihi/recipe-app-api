"""
Views for the user API
"""
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    # create/ にrequestが来た際に、UserSerializerのcreateメソッドが対応する。
    # CreateAPIView: データベースにObjectを追加するためのPostリクエストを作成するView
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""
    # token/ にrequestが来た際に、AuthTokenSerializerのvalidateメソッドが対応する。
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    # RetrieveUpdateAPIView: データベースのobjectをget,put又はpatchするView
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
        # ユーザーが認証されているかどうかを確認するもの
    permission_classes = [permissions.IsAuthenticated]
        # 認証されたユーザーが、その操作をする権限を与えられているかを確認するもの

    def get_object(self):
        """Retrieve and return the authenticated user."""
        # 認証されると、self.requestに認証されたuserが入る。それをReturnするために上書きする（？）
        return self.request.user