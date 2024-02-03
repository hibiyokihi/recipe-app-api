"""
Views for the recipe APIs.
"""
from rest_framework import (
    viewsets,
    mixins,
    # mixinsは、view(ViewSet)にfunctionalityを追加するもの。
)
# viewsets.ViewSetクラスを使う場合、CRUD操作のGETやPOST等のメソッドの代わりにアクションを使う。
# get() = list(), post() = create()など
from rest_framework.authentication import TokenAuthentication
# Tokenの方法で認証を行う。
from rest_framework.permissions import IsAuthenticated
# 認証済みのuserがrecipeのエンドポイントを使う前に権限をチェックする。is authorizedの意味？

from core.models import (
    Recipe,
    Tag,
    Ingredient
)
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """Views for manage recipe APIs"""
    # ModelViewSetクラスは以下のアクションを提供する。
    # list(), retrieve(), create(), update(), partial_update(), destroy()

    serializer_class = serializers.RecipeDetailSerializer
    # CLUD処理を通じて、ListよりもDetailを使うことが多いため、Detailをデフォルト値にする。
    queryset = Recipe.objects.all()
    # このViewset（API）で使用するオブジェクトを規定する。このケースでは全てのオブジェクト。
    authentication_classes = [TokenAuthentication]
    # TokenによるauthenticationがFalseならエラーを返す。
    permission_classes = [IsAuthenticated]
    # authenticateされていたら、このエンドポイント（API)を利用する権限を与える。未認証ならエラーを返す。

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        # デフォルトではquerysetに指定された全てのオブジェクトを取得する。これを上書きする。
        return self.queryset.filter(user=self.request.user).order_by('-id')
        # 本件ではquerysetは全ての認証ユーザーのレシピが取得されるから、このログインユーザーのレシピ限定でID降順で取得する。

    def get_serializer_class(self):
        """Return the serializer class for request."""
        # デフォルトではself.serializer_classをリターンするが、listアクションの時はRecipeSerializerを返すよう上書き。
        if self.action == 'list':
            return serializers.RecipeSerializer
            # クラスを呼び出すだけで実行しないこと。Instansiateするとオブジェクトをリターンするが、これだと動かない。

        return self.serializer_class
        # nameが{basename}-listでGETならlist()アクションが発動し、全体のSerializerが対応
        # nameが{basename}-detailでGETならretrieve()アクションが発動し、DetailのSerializerが対応

    def perform_create(self, serializer):
        """Create a new recipe."""
        # Viewsetを使ってモデルオブジェクトをCreateしてSaveする際に呼ばれるメソッド。これを上書き。
        # 引数のserializerは、validateされたデータが含まれる。
        serializer.save(user=self.request.user)
        # user情報は、serializerがvalidateしたデータには含まれていない。requestから取ってきて他のデータと一緒にSaveする。
        # serializerがvalidateしてSaveするデータは、serializerのfieldsで指定された項目だろう。おそらく。Userは含まれてない。


class TagViewSet(mixins.DestroyModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """Manage tags in the database."""
    # ModelViewSetは全てのアクションを提供するが、ここではover killなので、Generic＋Mixin(アクションの追加)を使用。
    # Mixinを使う場合には、GenericViewSetの前に全てのMixinを記載すること。
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')
