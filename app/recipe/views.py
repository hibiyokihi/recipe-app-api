"""
Views for the recipe APIs.
"""
from rest_framework import viewsets
# viewsetsはモデルに対してCRUD操作をする際に使用される
# viewsetsは複数のエンドポイントを持てる　⇔ APIViewは一つのエンドポイントのみ？
from rest_framework.authentication import TokenAuthentication
# Tokenの方法で認証を行う。
from rest_framework.permissions import IsAuthenticated
# 認証済みのuserがrecipeのエンドポイントを使う前に権限をチェックする。is authorizedの意味？

from core.models import Recipe
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """Views for manage recipe APIs"""
    serializer_class = serializers.RecipeDetailSerializer
    # CLUD処理を通じて、ListよりもDetailを使うことが多いため、Detailをデフォルト値にする。
    queryset = Recipe.objects.all()
    # このViewset（API）で使用するオブジェクトを規定する。このケースでは全てのオブジェクト。
    authentication_classes = [TokenAuthentication]
    # Tokenによる認証を通ったら、authenticatedとされる。認証エラーならエラーを返す。
    permission_classes = [IsAuthenticated]
    # authenticateされていたら、このエンドポイント（API)を利用する権限を与える。未認証ならエラーを返す。

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        # デフォルトではquerysetに指定された全てのオブジェクトを取得する。これを上書きする。
        return self.queryset.filter(user=self.request.user).order_by('-id')
        # 本件ではquerysetは全ての認証ユーザーのレシピが取得されるから、このログインユーザーのレシピ限定でID降順で取得する。

    def get_serializer_class(self):
        """Return the serializer class for request."""
        # この関数はデフォルトではself.serializer_classをリターンするが、リスト又は詳細を返せるように上書きする。
        if self.action == 'list':
            return serializers.RecipeSerializer
            # クラスを呼び出すだけで実行しないこと。Instansiateするとオブジェクトをリターンするが、これだと動かない。

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        # Viewsetを使ってモデルオブジェクトをCreateしてSaveする際に呼ばれるメソッド。これを上書き。
        # 引数のserializerは、validateされたデータが含まれる。
        serializer.save(user=self.request.user)
        # user情報は、serializerがvalidateしたデータには含まれていない。requestから取ってきて他のデータと一緒にSaveする。
        # serializerがvalidateしてSaveするデータは、serializerのfieldsで指定された項目だろう。おそらく。Userは含まれてない。
