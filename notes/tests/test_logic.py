"""Тестирование (unittest) логики проекта yanote."""

from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING

# Получаем модель пользователя.
User = get_user_model()

# Название и текст заметок вынесем в константы модуля.
NOTE_TITLE = 'Заметка'
NOTE_TEXT = 'Текст заметки'
NOTE_SLUG = 'slug'
NEW_NOTE_TITLE = 'Новая заметка'
NEW_NOTE_TEXT = 'Новый текст заметки'
NEW_NOTE_SLUG = 'new-slug'

# Страница редиректа:
REDIRECT_URL = reverse('notes:success')

# Страница создания заметки:
ADD_URL = reverse('notes:add')


class TestSlug(TestCase):
    """Тестирование генерации slug и создания заметок."""

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаём пользователя-автора и логиним его:
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Подготавливаем форму для создания заметки:
        cls.form_data = {'title': NOTE_TEXT,
                         'text': NOTE_TITLE,
                         'slug': NOTE_SLUG}
        # Подготавливаем форму для создания заметки без slug:
        cls.form_data_without_slug = {'title': NOTE_TITLE, 'text': NOTE_TEXT}
        # Подготавливаем форму для создания заметки с существующим slug:
        cls.form_data_exist_slug = {'title': NEW_NOTE_TEXT,
                                    'text': NEW_NOTE_TITLE,
                                    'slug': NOTE_SLUG}

    def test_slug_generation(self):
        """Проверка генерации slug из title."""
        # POST запрос на создание заметки без slug:
        response = self.author_client.post(ADD_URL,
                                           data=self.form_data_without_slug)
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, REDIRECT_URL)
        # Учитываем количество созданных заметок:
        count_notes = 1
        # Получаем количество заметок из БД:
        count_notes_from_db = Note.objects.count()
        # Проверяем количество заметок:
        self.assertEqual(count_notes_from_db, count_notes)
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data_without_slug['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)

    def test_slug_unique(self):
        """Проверка уникальности slug."""
        # Создаём первый объект заметки:
        Note.objects.create(title=NOTE_TITLE,
                            text=NOTE_TEXT,
                            slug=NOTE_SLUG,
                            author=self.author)
        # Фиксируем количество созданных заметок:
        count_notes = 1
        # Создаем вторую заметку с тем же slug:
        response = self.author_client.post(ADD_URL,
                                           data=self.form_data_exist_slug)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(self.form_data_exist_slug['slug'] + WARNING))
        # Получаем количество заметок из БД:
        count_notes_from_db = Note.objects.count()
        # Убеждаемся, что заметка не создана:
        self.assertEqual(count_notes_from_db, count_notes)

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создавать заметки."""
        # В POST-запросе отправляем данные, полученные из фикстуры form_data:
        response = self.author_client.post(ADD_URL, data=self.form_data)
        # Проверяем, что редирект привёл к странице 'успешно':
        self.assertRedirects(response, REDIRECT_URL)
        # Фиксируем в переменной, количество созданных записей:
        count_notes = 1
        # Получаем количество заметок из БД:
        count_notes_from_db = Note.objects.count()
        # Убеждаемся, что заметка создана:
        self.assertEqual(count_notes_from_db, count_notes)
        # Получаем объект заметки из БД:
        new_note = Note.objects.get()
        # Сверяем атрибуты объекта с ожидаемыми.
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создавать заметки."""
        # Через анонимного клиента пытаемся создать заметку:
        response = self.client.post(ADD_URL, data=self.form_data)
        # Проверяем, что редирект привёл к странице логина:
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={ADD_URL}'
        self.assertRedirects(response, expected_url)
        # Фиксируем в переменной, что заметка не создана:
        count_notes = 0
        # Получаем количество заметок из БД:
        note_count_from_db = Note.objects.count()
        # Убеждаемся, что заметка не создана:
        self.assertEqual(note_count_from_db, count_notes)


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

        # Формируем данные для POST-запроса по редактированию заметки.
        cls.form_data = {'title': NEW_NOTE_TITLE,
                         'text': NEW_NOTE_TEXT,
                         'slug': NEW_NOTE_SLUG}

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        # Выполняем POST запрос на редактирование от имени автора заметки:
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем редирект:
        self.assertRedirects(response, REDIRECT_URL)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать заметку другого автора."""
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что страница не найдена:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем объект запросом из БД:
        note_from_db = Note.objects.get(pk=self.note.pk)
        # Проверяем, что атрибуты объекта из БД и из фикстуры равны:
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        # От имени автора заметки отправляем DELETE-запрос на удаление:
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к странице 'успешно':
        self.assertRedirects(response, REDIRECT_URL)
        # Проверяем статус-код ответа:
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Фиксируем в переменной, что заметка удалена:
        count_notes = 0
        # Получаем количество заметок из БД:
        note_count_from_db = Note.objects.count()
        # Убеждаемся, что заметка удалена:
        self.assertEqual(note_count_from_db, count_notes)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалить заметку другого автора."""
        # От имени не автора заметки отправляем DELETE-запрос на удаление:
        response = self.reader_client.delete(self.delete_url)
        # Проверяем статус-код ответа:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Фиксируем в переменной, что заметка не удалена:
        count_notes = 1
        # Получаем количество заметок из БД:
        note_count_from_db = Note.objects.count()
        self.assertEqual(note_count_from_db, count_notes)
