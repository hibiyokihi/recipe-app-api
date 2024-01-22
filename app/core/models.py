"""
Database models.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    """Manager for users"""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # extra_fieldsはkwargs。辞書で渡すと=の形で展開してくれる
        user.set_password(password)
        # テキストのpassをハッシュするメソッド
        user.save(using=self._db)
        # usingは複数のDBを扱う場合のお決まり

        return user

    def create_superuser(self, email, password):
        """Create and return new superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system"""
    # 通常のモデルはModelクラスから作成するが、Userは特別。
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    # モデル名.objectsはデフォルトではそのモデルのインスタンスを返すが、上書きする。
    # get_user_model().objects.メソッド名で、UserManagerで規定したメソッドを呼び出せる。

    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    """Recipe object"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # 第一引数は参照するモデル。settings.pyで'core.User'を指定している。
        # get_user_model()と同様、User参照先に変更があった場合にもコードに影響が出ない。
        on_delete=models.CASCADE,
        # 参照先のUserインスタンスが削除された場合には、関連するRecipeインスタンスも削除する
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title
