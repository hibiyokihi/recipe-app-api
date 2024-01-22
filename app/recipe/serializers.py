"""
Serializers for recipe APIs
"""
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe."""
    # このserializerにRecipeモデルのリストを渡すと、validateしてデータを返す。

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', "price", "link"]
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detial view."""
    # RecipeSerializeをベースにするから、追加部分だけを記載すれば良い。

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
