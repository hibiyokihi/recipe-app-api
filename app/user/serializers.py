"""
Serializers for the user API view.
"""
from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.utils.translation import gettext as _

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""
    # Serializerとは、jsonを受け取って、内容をvalidateして、python object又はdatabase Modeにconvertするもの。
    # Modelインスタンスにコンバートする際は、ModelSerializerを使って、Metaでモデルとvalidationルールを規定する。
    # Model意外の場合は、Selializerクラスを使う。

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
        # ModelSerializerは、Metaで規定したvalidation実行後にcreateやupdateメソッドでModelにコンバートする。
        # Passはread(get)できては困るから、write_onlyでコンバートする。
        # Validationを通過しなかった場合は、400 BAD REQUESTを返す。

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)
        # Metaで規定したvalidationを通過後のデータがvalidated_dataとして渡される。validateエラーがあれば実行されない。
        # superのcreateメソッドをそのまま使う場合は上書きする必要ない。
        # デフォルトではserializerはパスワードをHashせずにTextのままモデルに保存するため、ハッシュ機能を追加するため上書き。

    def update(self, instance, validated_data):
        # instanceは変更される側のデータ。validated_dataは入力された変更データ。
        """Update and return user."""
        password = validated_data.pop('password', None)
            # validated_data辞書からpaswordを抜く意味もあるからgetではなくpopを使う。
        user = super().update(instance, validated_data)
            # update機能自体は上書きする必要ないからsuperのupdateを使う。validated_dataはpassを抜かれた後のもの。
            # passはハッシュ処理する必要があるから、別途set_passwordにより上書きしている。

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )
    # ModelSerializerはモデル側でスキーマ設定してあるが、Serializerの場合は設定する。

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        # validationにはデフォルトでusernameとpasswordが必要であり、本ケースではemailをusernameとして使っている。
        # authenticateが通れば、tokenがreturnされる。通らなければnullが帰る。
        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code="authorization")

        attrs['user'] = user
        # "user"ではなく'token'では？？
        return attrs
