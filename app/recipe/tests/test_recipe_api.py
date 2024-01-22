"""
Tests for recipe APIs
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse('recipe:recipe-list')
# リターンされるurlはどういう形？（要確認）
# recipe-listというurl名はrouterが自動で作成した？（要確認）


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    # 引数にidを渡す必要があるため、定数ではなく関数にする必要がある。
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    # apiテストをサポートするため、apiを使わずに直接モデルに新しいレシピを追加する関数を作る。
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    # test目的でdefaultsを設定しているだけ。Testでいちいちフィールドを入力するのは面倒だから。
    defaults.update(params)
    # paramsで変更内容が渡されたらデフォルトの内容をupdateする。

    recipe = Recipe.objects.create(user=user, **defaults)
    # デフォルトの内容か、変更があればアップデート後の辞書が渡される。
    # （仮説）モデルにはデフォルトでcreateメソッドがあり、モデル名.objects.createで呼び出せる。
    # データベースに新規保存した上でrecipe変数に格納する。
    return recipe


def create_user(**params):
    get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123'
        )

        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        # テスト用にdefault設定してあるから、Paramsは渡さなくてOK。２つサンプルを作ってる。
        # この関数は新規レシピをリターンするが、ここではデータベースに保存するだけでOK。
        res = self.client.get(RECIPES_URL)
        # apiを使って

        recipes = Recipe.objects.all().order_by('-id')
        # Recipeインスタンスを全て取得して、降順に並べる（マイナスをつけると降順）。最新のがトップに。
        serializer = RecipeSerializer(recipes, many=True)
        # apiを通さずDBから直接取得したデータをserializerでValidateする。
        # 一つのアイテムの詳細データかデータリストを渡せる。many=Trueはデータリストを渡すことを知らせる。

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        # authenticateされたUserにより作られたレシピだから、apiからデータが返ってくるはず。それをテストする。

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='testpass123',
        )
        create_recipe(user=other_user)
        # authenticateされていないユーザーによるCreate　→エラーになるべき。
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        # self.userにより作成されたレシピのみが返ってくるはず。

        recipes = Recipe.objects.filter(user=self.user)
        # apiを通さず、直接DBからself.userのレシピだけを抽出
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        # other_userによるレシピが作成されていたら（res.dataに含まれいたら）エラーになる。

    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        # 一つのレシピだけを渡すから、many=Trueは記載しない。
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        # apiから取得したデータと、モデルから直接取得したデータが等しいことをテストする。

    def test_create_recipe(self):
        """Test creating a recipe."""
        # apiを使ってcreateできることをテストするのであり、create_recipeで直接モデルを操作するのではない。
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECIPES_URL, payload)
        # postに成功すると追加したdataがリターンされる。

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # 201はデータのCreateが成功した時のコード。
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
            # getattrに辞書とKeyを渡すと、対応するValueがリターンされる。全てのKey-Valueの一致を確認する。
            # recipe.titleのようなアクセスはできるが、recipe.kやrecipe[k]のように変数は使えないからgetattrを使う。
            # getattrの方はモデルから直接取得したデータ、vはpayloadだからapiでPostして返ってきたデータ。
        self.assertEqual(recipe.user, self.user)
        # recipe.userはモデルから直接取得したユーザー情報、self.userはTestCaseで作成、authenticate、Postしたユーザー。

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        # patchは一部を変更する場合。putは全体を変更する場合。

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        # patchによりDBは更新されているものの、recipeは更新前のオブジェクトのまま。
        # recipe = Recipe.objects.get(条件)で再取得するのは面倒だから、refresh_from_db()で更新後のものを取得。
        self.assertEqual(recipe.title, payload['title'])
        # recipeはモデル側で更新後のデータ、payloadはapiがpatchに使ったデータ。
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='http://example.com/recipe.pdf',
            description="Sample recipe description",
        )

        payload = {
            "title":'New recipe title',
            "link":'http://example.com/new-recipe.pdf',
            "description":"New-recipe description",
            "time_minutes": 10,
            "price": Decimal('2.50'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
