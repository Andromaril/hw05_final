from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='Jack')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест текст',
            group=cls.group,
        )
        cls.form = PostForm()
        cls.comment = Comment.objects.create(author=cls.user1,
                                             text='Тест', post=cls.post)
        cls.form2 = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_form_create(self):
        """Проверка создания поста в базе данных."""

        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тест текст',
            'group': self.group.pk,
            'image': uploaded

        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.context.get('page_obj')[1].text,
                         form_data.get('text'))
        self.assertEqual(response.context.get('page_obj')[1].group, self.group)

        self.assertIn("<img", response.content.decode()) 

        self.assertEqual(Post.objects.count(), 2)
        self.assertRedirects(
            response, reverse('posts:profile',
                              args=(self.user.username,)))

    def test_form_edit(self):
        """Проверка создания комментария."""

        form_data = {
            'text': 'Тест_текст',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    args=(self.post.pk,)),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.context.get('comment')[1].text,
                         form_data.get('text'))
   

        self.assertEqual(Comment.objects.count(), 2)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              args=(self.post.pk,))
        )
