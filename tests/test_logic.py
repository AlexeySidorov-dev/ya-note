"""Тестирование логики проекта yanote."""

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()

# Название и текст заметок вынесем в константы модуля.
NOTE_TITLE = 'Заметка'
NOTE_TEXT = 'Текст заметки'
NEW_NOTE_TITLE = 'Редактированная заметка'
NEW_NOTE_TEXT = 'Редактированный текст заметки'


class TestSlug(TestCase):
    """Тестирование генерации slug."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаём пользователя-автора.
        cls.author = User.objects.create(username='Автор')
        # Создаем заметку без slug.
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            author=cls.author)

    def test_slug_generation(self):
        """Проверка генерации slug из title."""
        # Ожидаемый slug.
        expected_slug = slugify(self.note.title)[:100]
        self.assertEqual(self.note.slug, expected_slug)

    def test_slug_unique(self):
        """Проверка уникальности slug."""
        # Создаем вторую заметку с названием первой заметки, slug генерируется
        # из названия автоматически, а значить он будет совпадать с первой
        # заметкой.
        with self.assertRaises(Exception):
            Note.objects.create(title=NOTE_TITLE,
                                text=NOTE_TEXT,
                                author=self.author)


class TestNoteCreation(TestCase):
    """Тестирование заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Сохраняем в переменную страницу создания заметки.
        cls.add_url = reverse('notes:add')
        # Создаём пользователя-автора и авторизуем его.
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Данные для POST-запроса при создании заметки.
        cls.form_data = {'title': NOTE_TITLE,
                         'text': NOTE_TEXT}

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создавать заметки."""
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы.
        self.client.post(self.add_url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметок в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создавать заметки."""
        # Совершаем запрос через авторизованный клиент.
        response = self.author_client.post(self.add_url, data=self.form_data)
        # Проверяем, что редирект привёл к странице 'успешно'.
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем количество комментариев.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть один комментарий.
        self.assertEqual(notes_count, 1)
        # Получаем объект комментария из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.title, NOTE_TITLE)
        self.assertEqual(note.text, NOTE_TEXT)
        self.assertEqual(note.author, self.author)


class TestNodeEditDelete(TestCase):
    """Тестирование редактирования и удаления заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаём пользователя - автора заметки.
        cls.author = User.objects.create(username='Автор')
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём заметку.
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            author=cls.author
        )
        # URL для редактирования заметки.
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        # URL для удаления заметки.
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        # URL редиректа.
        cls.success_url = reverse('notes:success')
        # Формируем данные для POST-запроса по обновлению заметки.
        cls.form_data = {'title': NEW_NOTE_TITLE,
                         'text': NEW_NOTE_TEXT}

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к странице 'успешно'.
        self.assertRedirects(response, self.success_url)
        # Заодно проверим статус-коды ответов.
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалить заметку другого автора."""
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        # Выполняем запрос на редактирование от имени автора заметки.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.success_url)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.title, NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать заметку другого автора."""
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.title, NOTE_TITLE)
        self.assertEqual(self.note.text, NOTE_TEXT)
