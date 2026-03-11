"""Тестирование контента проекта yanote."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

# Получаем модель пользователя.
User = get_user_model()


class TestNotes(TestCase):
    """Тестирование страницы заметок пользователя."""
    # Количество заметок автора сохраняем в атрибут класса.
    COUNT_NOTES = 3

    @classmethod
    def setUpTestData(cls):
        """Создание фикстур."""
        # Создаем два пользователя и по 3 заметки от каждого пользователя.
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        # Создаем заметки по одной, чтобы сработал метод save().
        users = (cls.author, cls.reader,)
        for user in users:
            for index in range(cls.COUNT_NOTES):
                Note.objects.create(
                    title=f'Заметка {index} от автора {user}',
                    text='Текст заметки',
                    author=user
                )

        # Создаём клиент для автора.
        cls.author_client = Client()
        # "Логиним" автора в клиенте.
        cls.author_client.force_login(cls.author)
        # Загрузим из БД первую заметку автора.
        cls.note = Note.objects.filter(author=cls.author).first()

    def test_notes_only_author(self):
        """В списке отображаются только заметки автора."""
        # Сохраняем в переменную адрес страницы с заметками.
        list_notes_url = reverse('notes:list')
        # Загружаем страницу с заметками.
        response = self.author_client.get(list_notes_url)
        # Получаем объекты из контекста.
        object_list = response.context['object_list']
        # Получаем заметки только автора из БД.
        notes_author = Note.objects.filter(author=self.author)
        # Сравниваем отсортированные queryset.
        self.assertQuerySetEqual(object_list.order_by('id'),
                                 notes_author.order_by('id'))
        # Проверяем количество заметок.
        self.assertEqual(object_list.count(), self.COUNT_NOTES)

    def test_detail_note(self):
        """Контент на странице заметки."""
        # Сохраняем в переменную адрес страницы с заметкой.
        url = reverse('notes:detail', args=(self.note.slug,))
        # Загружаем страницу с заметкой.
        response = self.author_client.get(url)
        # Получаем объект из контекста.
        object = response.context['object']
        # Сравниваем объект с выгруженной из БД заметкой.
        self.assertEqual(object, self.note)

    def test_author_has_form(self):
        """При создании и редактировании заметки автору передается форма."""
        # Сохраняем в кортеж страницы создания и редактирования заметки.
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, slug in urls:
            with self.subTest(name=name):
                url = reverse(name, args=slug)
                # Загружаем страницу.
                response = self.author_client.get(url)
                # Проверяем, что форма есть в контексте.
                self.assertIn('form', response.context)
                # Проверяем, что объект формы соответствует нужному
                # классу формы.
                self.assertIsInstance(response.context['form'], NoteForm)

    def test_delete_note(self):
        """Автору передается контекст при удалении заметки."""
        # Сохраняем в переменную адрес страницы удаления заметки.
        url = reverse('notes:detail', args=(self.note.slug,))
        # Загружаем страницу с заметкой.
        response = self.author_client.get(url)
        # Проверяем, что контент передается.
        self.assertIsNotNone(response.context)

    def test_anonymous_client_has_not_form(self):
        """Анонимному пользователю контекст не передается."""
        # Сохраняем в кортеж страницы создания и редактирования заметки.
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:list', None),
        )
        for name, slug in urls:
            with self.subTest(name=name):
                url = reverse(name, args=slug)
                response = self.client.get(url)
                self.assertIsNone(response.context)
