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
# prefixと、対応するviewsetを指定する。
# /api/recipe/recipesにGET >> ViewSetクラスのlist()アクション／nameはrecipe-list（prefixの単数形で作成される）
# /api/recipe/recipesにPOST >> create()アクション／nameはrecipe-list
# /api/recipe/recipes/{id}にGET >> retrieve()アクション／nameはrecipe-detail
# /api/recipe/recipes/{id}にPUT(PATCH) >> update()アクション／nameはrecipe-detail
# /api/recipe/recipes/{id}にDELETE >> destroy()アクション／nameはrecipe-detail

router.register('tags', views.TagViewSet)
# /api/recipe/tags

router.register('ingredients', views.IngredientViewSet)
# /api/recipe/ingredients

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
