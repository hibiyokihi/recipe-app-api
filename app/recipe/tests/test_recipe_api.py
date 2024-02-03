"""
Tests for recipe APIs
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse('recipe:recipe-list')
# routerはrecipesで登録してるけど、recipe-listとなることに注意。urlはrecipe/。


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    # 引数にidを渡す必要があるため、定数ではなく関数にする必要がある。
    return reverse('recipe:recipe-detail', args=[recipe_id])
    # recipe/{recipe_id}のエンドポイントをリターンする


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
    # （仮説）モデルにはデフォルトでcreateメソッドがあり、モデル名.objects.createでインスタンスを作れるのだろう。
    return recipe
    # データベースに新規保存した上でrecipe変数をリターンする。


def create_user(**params):
    return get_user_model().objects.create_user(**params)


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
        # self.clientは、self.userのユーザー情報で認証されている状態。
        # よって、self.client.get等のリクエストは、認証ユーザーself.userによるリクエストとなる。

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        # テスト用にdefault設定してあるから、Paramsは渡さなくてOK。２つサンプルを作ってる。
        # この関数は新規レシピをリターンするが、ここではデータベースに保存するだけでOK。
        res = self.client.get(RECIPES_URL)
        # {basename}-listのURLにGETするとModelViewSetのlist()アクションが発動し、get_queryset()がリターン
        # →RecipeViewSetでquerysetは全体を取得、get_queryset()はquerysetをフィルター後。list()はどっちをリターンする？

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
        # authenticateされていないユーザーによるCreate　→Createされないべき
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
            "title": 'New recipe title',
            "link": 'http://example.com/new-recipe.pdf',
            "description": "New-recipe description",
            "time_minutes": 10,
            "price": Decimal('2.50'),
        }
        url = detail_url(recipe.id)
        # recipe/{recipe.id}
        res = self.client.put(url, payload)
        # 上記のurlパターンにPUTすると、ViewSetクラスのUpdateアクションが発動する

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        # refreshしないと、DBはupdateされても変数recipeは変更前のまま
        # refresh後、recipeとpayloadは同じになっているはず（userを除いて）　→テスト
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)
        # userはpayloadには含まれていないから、別途テストする

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        # レシピのuserは変更されるべきではないから、ユーザーの変更ができないことを確認する。
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        # user情報がpatchにより変更されていないことを確認

    def test_delete_recipe(self):
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)
        # recipe-detailに対してdelete()するとdestroyアクションが発動する。

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # deleteが成功するとHTTP204が返る。該当のアイテムがDBに無くなってるからno content
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())
        # DBに残っていないか確認。filter()だけだとfalseは返らないからexists()を使う。

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete other users recipe gives error."""
        other_user = create_user(email='user3@example.com', password='test123')
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        # tagがオブジェクトのネストになっているから、これをjson形式でPostするためFormat設定。
        # recipe/のエンドポイントにPOSTリクエスト→ create()アクション
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        # authenticated userが作成したrecipeに限定する。（そもそも未認証ならrecipe作成できないのでは？）
        self.assertEqual(recipes.count(), 1)
        # このテストを先にしておかないと、recipes[0]でエラーが生じる。
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating recipe with existing tags."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Indian Curry',
            'time_minutes': 50,
            'price': Decimal('3.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        # tagsをRecipeのManyToManyFieldに設定すると、recipe.tags.からTagモデルを操作できるということ？
        # recipe.tags.count() ... Tag.objects.count()になる？
        # recipe.tags.all() ... Tag.objects.all()になる？
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())
        # 通常、recipeに対してrefresh_from_dbが必要になるが、ManyToManyの場合は不要。
        # 理由は、recipe.tags.all()は新しいクエリを作成することになり、キャッシュを使わないからrefreshが必要ないため。
        # Tagモデルにインスタンスが作られたこと、Recipeインスタンスに紐づいていることをテストする。

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        # 最初に、recipeのtagsにはBreakfastタグを設定する。

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        # patchにより、recipeのtagsをLunchタグに上書きする。予めTagモデルにLunchを作ってから、それを指定。

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())
        # Tagモデルには両方のTagインスタンスが残っているが、recipe.tagsにはpatch後のLunchタグが残っている。

    def test_clear_recipe_tags(self):
        """Test clearing a recipes tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        # recipe.tagsはManyToManyだから新しいクエリが発生。よってrecipeのrefreshは不要。

    def test_create_recipe_with_new_ingredients(self):
        """Test creating recipe with new ingredients."""

        recipe = create_recipe(user=self.user,
                               ingredients=Ingredient.objects.create(
                                   user=self.user,
                                   name='Banana'
                               ))

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating recipe with existing ingredients."""
        pass

    def test_create_ingredients_on_update(self):
        """Test creating tag when updating a recipe."""
        pass

    def test_update_recipe_assign_ingredients(self):
        """Test assigning an existing tag when updating a recipe."""
        pass

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipes ingredients."""
        pass
