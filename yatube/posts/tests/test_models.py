from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='Jack')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый текст', post=cls.post)
        cls.follow = Follow.objects.create(author=cls.user, user=cls.user1)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        expected_object_name = group.title
        expected_text = post.text
        expected_comment = comment.text
        expected_follow = follow.user.username
        self.assertIsInstance(expected_object_name, str)
        self.assertIsInstance(expected_text, str)
        self.assertIsInstance(expected_comment, str)
        self.assertIsInstance(expected_follow, str)
