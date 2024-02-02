"""
URL Mapping for the Recipe API.
"""
from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)
# basenameと、対応するviewsetを指定する。
# {basename}にGETがあればViewSetクラスのアクションlist()が発動する。
# {basename}にPOSTがあればViewSetクラスのアクションcreate()が発動する。
# {basename}/{id等}にGETがあればretrieve()、PUTがあればupdate()のアクションが発動する。
router.register('tags', views.TagViewSet)
# TagViewSetは機能をlistアクションに絞ってるから、/tagに対するGETのみを想定している。


app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
    # reverseによりエンドポイントを取得し、URL nameはDefaultRouterが自動対応する。
    # URL名 {basename}-listにGETがあればlist()アクション、POSTがあればcreateアクション。
    # URL名 {basename}-detailにGETがあればretrieve、PUTがあればupdate。詳細はDocs参照。
]
