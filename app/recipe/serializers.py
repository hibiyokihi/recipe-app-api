"""
Serializers for recipe APIs
"""
from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag."""
    # RecipeSerializerの中でTagSerializerを使うから、上に持ってくる必要がある。

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe."""
    # serializerとは、モデル（DB）とreq, resの間に入り、データを変換したりvalidateしたりするもの。
    # Recipeモデルのデータを渡すとserializerをリターンし、serializer.dataでvalidate後のデータを得る。
    # list以外のcreateやupdateアクションの場合はDetailの方が対応するが、Detailはこのserializerを継承してるからここを上書き。
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', "price", "link", "tags"]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags as needed."""
        # createとupdateに共通するコードをまとめるためのヘルパーFn。外で使うことを想定しないため、_を頭につける。
        auth_user = self.context['request'].user
        # viewがserializerにuser情報を与える時にはcontext['request]を使う
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                # その名の通り、すでに同じtagがあればretrieveし、無ければ新規にTagインスタンスをcreateする。
                # tag_objには、既にDBにある、又は新規に作成されたTagインスタンスが入る。
                # createdはここでは使わないが、get_or_create()はこのタプルをリターンするのだろう。
                user=auth_user,
                **tag,
                # name=tag['name']としてもここでは同じだが、将来的にTagに新しいフィールドができるかもしれないから**を使う。
            )
            recipe.tags.add(tag_obj)
            # recipeのtagsフィールドにタグを追加している。

    def create(self, validated_data):
        """Create a recipe."""
        # recipe/に対してPOSTがあった時のアクション。post dataをvalidate後にvalidated_dataを受け取ってDBに保存する。
        # デフォルトでは、ネストされたserializerはread-only。よってRecipeをcreateする際にTagを新規作成することができない。
        # これを変更するためにcreateメソッドを上書きする。
        tags = validated_data.pop('tags', [])
        # 辞書に対してpopを使う場合、第一で指定したKeyが無かった場合に返す値を指定する。ここではtagsキーが無ければ[]を返す。
        recipe = Recipe.objects.create(**validated_data)
        # popしたからvalidated_dataからはtagsは抜いてある。重複してTagを作ることを防ぐため。
        self._get_or_create_tags(tags, recipe)
        # recipeインスタンスにtagsフィールドを追加する。新規のタグがあればDBに保存し、既存タグならretrieveして使う。

        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""
        # instanceは現状のデータ、validatec_dataが変更後のデータ
        tags = validated_data.pop('tags', None)
        # []とNoneは同じ。is not Noneを使うためにここではNoneとした。
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
            # instanceからtagsを消し、新たにvalidated_dataのtagsを追加する。新規タグはDBに保存する。

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            # instanceのkey, valueをvalidated_dataのもので上書きする。tagsはpop()で除かれているから上書きされない。

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detial view."""
    # RecipeSerializeをベースにするから、追加部分だけを記載すれば良い。

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
