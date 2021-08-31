from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostsViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='Jack')
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
            image=uploaded,
        )

        cls.comment = Comment.objects.create(author=cls.user1,
                                             text='Тестовый текст',
                                             post=cls.post)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    args=(self.group.slug,)): 'posts/group_list.html',
            reverse('posts:profile',
                    args=(self.user.username,)):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    args=(self.post.pk,)):
                        'posts/post_detail.html',
            reverse('posts:post_edit',
                    args=(self.post.pk,)):
                        'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.guest_client.get(reverse('posts:index'))

        self.assertEqual(response.context['page_obj'][0].text,
                         self.post.text)
        self.assertEqual(response.context['page_obj'][0].author, self.user)
        self.assertEqual(response.context['page_obj'][0].group, self.group)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.guest_client.get(reverse('posts:group_list',
                                                 args=(self.group.slug,)))

        self.assertEqual(response.context['page_obj'][0].text,
                         self.post.text)
        self.assertEqual(response.context['page_obj'][0].author,
                         self.user)
        self.assertEqual(response.context['page_obj'][0].group,
                         self.group)

        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(response.context['group'].description,
                         self.group.description)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = self.guest_client.get(reverse('posts:profile',
                                                 args=(self.user.username,)))

        self.assertEqual(response.context['page_obj'][0].author,
                         self.user)
        self.assertEqual(response.context['page_obj'][0].text,
                         self.post.text)
        self.assertEqual(response.context['page_obj'][0].group, self.group)

        self.assertEqual(response.context['author'].username,
                         self.user.username)

        self.assertEqual(response.context['count'], 1)
        self.assertEqual(response.context['following'], False)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом. Проверка на то,
           что только авторизованный пользователь может оставлять
           комментарий и он появляется на странице поста.
        """

        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=(self.post.pk,)))

        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(response.context.get('post').author, self.user)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').group, self.group)
        self.assertEqual(response.context.get('count'), 1)

        self.assertEqual(response.context['comment'][0].text,
                         self.comment.text)
        self.assertEqual(response.context['comment'][0].author.username,
                         self.user1.username)
        comment_obj = Comment.objects.filter(author=self.user1,
                                             post=self.post.pk).count()
        self.assertEqual(comment_obj, 1)

    def test_correct_context_create(self):
        """Шаблон create сформированы с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_context_post_edit(self):
        """Шаблон post_edit сформированы с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      args=(self.group.pk,)))

        self.assertTrue(response.context.get('is_edit'))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.user)
        self.assertEqual(response.context.get('post').group, self.group)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_appear_index_group_profile(self):
        """После создания поста он появляется
           на главной странице, страницах поста и профайла.
        """

        post_urls = (reverse('posts:index'),
                     reverse('posts:group_list', args=(self.group.slug,)),
                     reverse('posts:profile',
                             args=(self.user.username,)),

                     )

        for post_url in post_urls:
            with self.subTest(post_url=post_url):
                response = self.guest_client.get(post_url)

                self.assertEqual(response.context['page_obj'][0].text,
                                 self.post.text)
                self.assertEqual(response.context['page_obj'][0].author,
                                 self.user)
                self.assertEqual(response.context['page_obj'][0].group,
                                 self.group)

    def test__image_on_page(self):
        """После создания поста c картинкой она появляется
           на главной странице, страницах поста и профайла,
           странице отдельного поста.
        """
        post_urls = (reverse('posts:index'),
                     reverse('posts:group_list', args=(self.group.slug,)),
                     reverse('posts:profile',
                             args=(self.user.username,)),
                     reverse('posts:post_detail',
                             args=(self.post.pk,)),


                     )

        for post_url in post_urls:
            with self.subTest(post_url=post_url):
                response = self.guest_client.get(post_url)
                self.assertIn("<img", response.content.decode())

    def test_test_follow_auth(self):
        """Тест авторизованный пользователь не может
           подписаться на самого себя.
        """
        Follow.objects.create(user=self.user1, author=self.user)
        response = self.authorized_client.get(reverse('posts:profile_follow',
                                              args=(self.user.username,)))
        follower = Follow.objects.filter(user=self.user,
                                         author=self.user).count()
        self.assertEqual(follower, 0)
        self.assertNotIn('Подписаться',
                         response.content.decode())
        self.assertNotIn('Отписаться',
                         response.content.decode())

    def test_user_can_subscribe(self):
        """Тест авторизованный пользователь может
           подписаться на другого пользователя.
        """
        Follow.objects.create(user=self.user1, author=self.user)
        response = self.authorized_client.get(reverse('posts:profile',
                                              args=(self.user1.username,)))

        self.assertIn('Подписаться',
                      response.content.decode())
        self.assertNotIn('Отписаться', response.content.decode())

        response2 = self.authorized_client.post(reverse('posts:profile_follow',
                                                args=(self.user1.username,)),
                                                follow=True)

        follower = Follow.objects.filter(user=self.user1,
                                         author=self.user).count()
        self.assertEqual(follower, 1)

        self.assertIn('Отписаться', response2.content.decode())

    def test_user_can_unsubscribe(self):
        """Тест авторизованный пользователь может
           отписаться от другого пользователя.
        """
        Follow.objects.create(user=self.user, author=self.user1)
        follow = Follow.objects.filter(user=self.user,
                                       author=self.user1).count()
        self.assertEqual(follow, 1)
        response = self.authorized_client.post(reverse(
                                               'posts:profile_unfollow',
                                               args=(self.user1.username,)),
                                               follow=True)
        self.assertIn("Подписаться", response.content.decode())
        follow2 = Follow.objects.filter(user=self.user,
                                        author=self.user1).count()
        self.assertEqual(follow2, 0)

    def test_post_not_appear_in_index(self):
        """Новая запись пользователя не появляется в ленте тех,
           кто на него не подписан.
        """

        follow_index = self.authorized_client.get(reverse(
                                                  'posts:follow_index'))
        self.assertNotIn(self.post.text, follow_index.content.decode())

    def test_post_appear_in_index(self):
        """Новая запись пользователя появляется в ленте тех,
           кто на него подписан.
        """
        Follow.objects.create(user=self.user, author=self.user1)
        follow_index = self.authorized_client.get(reverse(
                                                  'posts:follow_index'))
        self.assertNotIn(self.post.text,
                         follow_index.content.decode())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        number_of_posts = 13
        for post in range(number_of_posts):
            cls.post = Post.objects.create(author=cls.user,
                                           text='Тестовая группа',
                                           group=cls.group,
                                           )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10.
           Проверка для страниц профайла, группы, главной страницы.
        """

        responses = (reverse('posts:index'),
                     reverse('posts:group_list',
                             args=(self.group.slug,)),
                     reverse('posts:profile',
                             args=(self.user.username,)))

        for adress in responses:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.PAGINATOR)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста.
           Проверка для страниц профайла, группы, главной страницы.
        """

        responses = (reverse('posts:index') + '?page=2',
                     reverse('posts:group_list',
                             args=(self.group.slug,)) + '?page=2',
                     reverse('posts:profile',
                             args=(self.user.username,)) + '?page=2',)

        for adress in responses:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_cache(self):
        """Тест проверяет работу кэша."""

        response = self.guest_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        self.assertContains(response, self.post.text)
        self.assertContains(response, self.group)

        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotContains(response, self.post.text)
        self.assertNotContains(response, self.group)
