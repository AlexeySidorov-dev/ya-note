"""Тестирование маршрутов проекта yanote."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):
    """Тестирование маршрутов и доступности страниц."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        # Создание заметки от имени автора.
        cls.notes = Note.objects.create(
            title='Тест',
            text='Текст для теста',
            slug='test',
            author=cls.author
        )

    def test_pages_availability_for_anonymous_client(self):
        """Доступность страниц для неавторизованного пользователя."""
        urls = (
            ('notes:home'),  # Главная страница.
            ('users:login'),  # Войти.
            ('users:signup'),  # Регистрация.
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_client(self):
        """Доступность страниц для авторизованного пользователя."""
        urls = (
            ('notes:home'),  # Главная страница.
            ('notes:list'),  # Список заметок.
            ('notes:add'),  # Новая заметка.
            ('notes:success'),  # Успешно.
        )
        # Логиним любого пользователя:
        self.client.force_login(self.author)
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_author(self):
        """Доступность страниц по правам пользователя."""
        users_statuses = (
            # автор комментария должен получить ответ OK
            (self.author, HTTPStatus.OK),
            # читатель должен получить ответ NOT_FOUND
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:edit', (self.notes.slug,)),  # Редактирование заметки.
            ('notes:detail', (self.notes.slug,)),  # Детали заметки.
            ('notes:delete', (self.notes.slug,)),  # Удаление заметки.
        )
        for user, status in users_statuses:
            # Логиним пользователя:
            self.client.force_login(user)
            for name, slug in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=slug)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_logout(self):
        """Выход пользователя logout."""
        url = reverse('users:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """Перенаправления для неавторизованного пользователя."""
        # Имена страниц, с которых ожидаем перенаправление на страницу логина.
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.notes.slug,)),
            ('notes:detail', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:list', None),
            ('notes:success', None),
        )

        for name, slug in urls:
            with self.subTest(name=name):
                # Сохраняем адрес страницы логина (перенаправление на нее).
                login_url = reverse('users:login')
                url = reverse(name, args=slug)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)


class TestRedirect(TestCase):
    """Тестирование редиректов при действиях с заметками."""
    # Тексты для заметок вынесем в атрибуты класса.
    NODE_TITLE = 'Заметка'
    NEW_NODE_TITLE = 'Заметка редактированная'
    NODE_TEXT = 'Текст заметки'
    NEW_NODE_TEXT = 'Текст заметки редактированный'

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создадим пользователя автора.
        cls.author = User.objects.create(username='Автор')
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Сохраняем адрес страницы для перенаправления после успешного
        # действия с заметкой.
        cls.redirect_url = reverse('notes:success')

        # Создаём заметку, которую будем редактировать и удалять в тестах.
        cls.note = Note.objects.create(
            title=cls.NODE_TITLE,
            text=cls.NODE_TEXT,
            author=cls.author
        )
        # Данные для POST-запроса при создании и редактировании заметки.
        cls.form_data = {'title': cls.NEW_NODE_TITLE,
                         'text': cls.NEW_NODE_TEXT}

    def test_redirect_after_add_note(self):
        """Редирект после создания заметки."""
        with self.subTest():
            url = reverse('notes:add')
            response = self.author_client.post(url, data=self.form_data)
            self.assertRedirects(response, self.redirect_url)

    def test_redirect_after_edit_note(self):
        """Редирект после редактирования заметки."""
        with self.subTest():
            url = reverse('notes:edit', args=(self.note.slug,))
            response = self.author_client.post(url, data=self.form_data)
            self.assertRedirects(response, self.redirect_url)

    def test_redirect_after_delete_note(self):
        """Редирект после удаления заметки."""
        with self.subTest():
            url = reverse('notes:delete', args=(self.note.slug,))
            response = self.author_client.delete(url)
            self.assertRedirects(response, self.redirect_url)
