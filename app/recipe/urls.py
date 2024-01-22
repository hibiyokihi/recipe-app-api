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
# recipes/ というエンドポイントを作成し、その先のエンドポイントに応じてRecipeViewSetが対応する。
# viewsetで作成したviewには、自動的にcreate, read, delete, updateのエンドポイントが作成される。

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
    # urlsはrouterによって自動的に作成される。create, read, delete, update?
]
