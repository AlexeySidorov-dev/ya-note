"""Тестирование (pytest) контента проекта yanote."""

import pytest
from pytest_lazyfixture import lazy_fixture as lf
from django.urls import reverse

from notes.forms import NoteForm


@pytest.mark.parametrize(
    'parametrized_client, note_in_list',
    (
        (lf('author_client'), True),
        (lf('not_author_client'), False),
    )
)
def test_notes_list_for_different_users(note, parametrized_client,
                                        note_in_list):
    """В списке отображаются только заметки автора и проверка контекста."""
    url = reverse('notes:list')
    # Выполняем запрос от имени параметризованного клиента:
    response = parametrized_client.get(url)
    # Получаем из контекста список объектов:
    object_list = response.context['object_list']
    # Проверяем истинность утверждения "заметка есть в списке".
    assert (note in object_list) is note_in_list


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),
        ('notes:edit', lf('slug_for_args'))
    )
)
def test_pages_contains_form(author_client, name, args):
    """При создании и редактировании заметки автору передается форма."""
    # Формируем URL:
    url = reverse(name, args=args)
    # POST запрос от имени автора на сформированную страницу:
    response = author_client.get(url)
    # Проверяем, есть ли объект формы в словаре контекста.
    assert 'form' in response.context
    # Проверяем, что объект формы относится к нужному классу.
    assert isinstance(response.context['form'], NoteForm)


def test_detail_note(author_client, slug_for_args, note):
    """Контекст на странице заметки."""
    # Страница отдельной заметки.
    url = reverse('notes:detail', args=slug_for_args)
    # Загружаем страницу с заметкой.
    response = author_client.get(url)
    # Получаем объект из контекста.
    object = response.context['object']
    # Сравниваем объект с заметкой фикстуры.
    assert object == note


def test_delete_note(author_client, slug_for_args):
    """Автору не передается контекст при удалении заметки."""
    # Страница удаления заметки:
    url = reverse('notes:delete', args=slug_for_args)
    # DELETE запрос от автора на удаление заметки:
    response = author_client.delete(url)
    # Проверяем, что контекст не передается.
    assert response.context is None


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),
        ('notes:edit', lf('slug_for_args')),
        ('notes:detail', lf('slug_for_args')),
        ('notes:delete', lf('slug_for_args')),
        ('notes:list', None),
    ),
)
def test_anonymous_client_has_not_form(client, name, args):
    """Анонимному пользователю контекст не передается."""
    # Формируем URL:
    url = reverse(name, args=args)
    # POST запрос от имени анонима на сформированную страницу:
    response = client.get(url)
    # Проверяем, что контекст не передается:
    assert response.context is None
