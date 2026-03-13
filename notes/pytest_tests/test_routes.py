"""Тестирование (pytest) маршрутов проекта yanote."""

import pytest
from pytest_django.asserts import assertRedirects
from pytest_lazyfixture import lazy_fixture as lf
from http import HTTPStatus

from django.urls import reverse


@pytest.mark.parametrize(
    'name',
    ('notes:home', 'users:login', 'users:signup', 'users:logout')
)
def test_pages_availability_for_anonymous_user(client, name):
    """Доступность страниц для неавторизованного пользователя."""
    url = reverse(name)  # Формируем URL.
    if name == 'users:logout':
        response = client.post(url)  # Выполняем post запрос.
    else:
        response = client.get(url)  # Выполняем get запрос.
    # Проверяем статус-код:
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(not_author_client, name):
    """Доступность страниц для авторизованного пользователя."""
    url = reverse(name)  # Формируем URL.
    response = not_author_client.get(url)  # Выполняем get запрос.
    # Проверяем статус-код:
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (lf('not_author_client'), HTTPStatus.NOT_FOUND),
        (lf('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
def test_pages_availability_for_different_users(
        parametrized_client, name, slug_for_args, expected_status):
    """Доступность страниц по правам пользователя."""
    url = reverse(name, args=slug_for_args)  # Формируем URL.
    response = parametrized_client.get(url)  # Выполняем get запрос.
    # Проверяем статус-код:
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:detail', lf('slug_for_args')),
        ('notes:edit', lf('slug_for_args')),
        ('notes:delete', lf('slug_for_args')),
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    ),
)
def test_redirects_for_anonymous_user(client, name, args):
    """Проверка редиректа для неавторизованного пользователя."""
    # Сохраняем адрес страницы логина (перенаправление на нее).
    login_url = reverse('users:login')
    url = reverse(name, args=args)  # Формируем URL.
    expected_url = f'{login_url}?next={url}'  # Якорь.
    response = client.get(url)  # Выполняем get запрос.
    # Ожидаем, что со всех проверяемых страниц анонимный клиент
    # будет перенаправлен на страницу логина:
    assertRedirects(response, expected_url)


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),  # Создание заметки.
        ('notes:edit', lf('slug_for_args')),  # Редактирование заметки.
        ('notes:delete', lf('slug_for_args')),   # Удаление заметки.
    ),
)
def test_redirect_after_change_note(author_client, form_data, name, args):
    """Редирект после действий с заметкой."""
    url = reverse(name, args=args)  # Формируем URL.
    # Страница редиректа после успешного действия с заметкой:
    redirect_url = reverse('notes:success')
    # Запросы от автора на действие с заметкой:
    if name == 'notes:delete':
        response = author_client.delete(url)  # DELETE запрос.
    else:
        response = author_client.post(url, data=form_data)  # POST запрос.
    # Проверяем редирект:
    assertRedirects(response, redirect_url)
