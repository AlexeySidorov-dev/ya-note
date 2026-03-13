"""Тестирование (unittest) контента проекта yanote."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

# Получаем модель пользователя.
User = get_user_model()


class TestNotes(TestCase):
    """Тестирование страницы заметок пользователя."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаем два пользователя:
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        # Создаем заметку от автора:
        cls.note = Note.objects.create(
            title='Заметка от автора',
            text='Текст заметки',
            author=cls.author
        )
        # Создаём клиент для пользователей:
        cls.author_client = Client()
        cls.reader_client = Client()
        # "Логиним" пользователей в клиенте:
        cls.author_client.force_login(cls.author)
        cls.reader_client.force_login(cls.reader)

    def test_notes_only_author(self):
        """В списке отображаются только заметки автора и проверка контекста."""
        users = (
            (self.author_client, True),
            (self.reader_client, False),
        )
        # Сохраняем в переменную адрес страницы с заметками.
        url = reverse('notes:list')
        for user, status in users:
            with self.subTest(user=user):
                # Загружаем страницу с заметками.
                response = user.get(url)
                # Получаем список объектов из контекста.
                object_list = response.context['object_list']
                # Проверяем истинность утверждения "заметка есть в списке".
                self.assertEqual(self.note in object_list, status)

    def test_author_has_form(self):
        """При создании и редактировании заметки автору передается форма."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, slug in urls:
            with self.subTest(name=name):
                url = reverse(name, args=slug)  # Формируем URL.
                # GET запрос от имени автора:
                response = self.author_client.get(url)
                # Проверяем, что форма есть в контексте.
                self.assertIn('form', response.context)
                # Проверяем, что объект формы соответствует нужному
                # классу формы.
                self.assertIsInstance(response.context['form'], NoteForm)

    def test_detail_note(self):
        """Контекст на странице заметки."""
        # Страница отдельной заметки:
        url = reverse('notes:detail', args=(self.note.slug,))
        # Загружаем страницу с заметкой.
        response = self.author_client.get(url)
        # Получаем объект из контекста.
        object = response.context['object']
        # Сравниваем объект с заметкой фикстуры.
        self.assertEqual(object, self.note)

    def test_delete_note(self):
        """Автору не передается контекст при удалении заметки."""
        # Страница удаления заметки:
        url = reverse('notes:delete', args=(self.note.slug,))
        # DELETE запрос от автора на удаление заметки:
        response = self.author_client.delete(url)
        # Проверяем, что контент не передается.
        self.assertIsNone(response.context)

    def test_anonymous_client_has_not_form(self):
        """Анонимному пользователю контекст не передается."""
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:list', None),
        )
        for name, slug in urls:
            with self.subTest(name=name):
                # Формируем URL:
                url = reverse(name, args=slug)
                # POST запрос от имени анонима на сформированную страницу:
                response = self.client.get(url)
                # Проверяем, что контекст не передается:
                self.assertIsNone(response.context)
