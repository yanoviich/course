import pytest
import json
from playwright.sync_api import sync_playwright

def load_test_data(file_path):
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)

def test_tc_01(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-01":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.fill("input[name='имя']", data["inputs"]["имя"])
            page.fill("input[name='фамилия']", data["inputs"]["фамилия"])
            page.fill("input[name='электронная почта']", data["inputs"]["электронная почта"])
            page.click("text=Зарегистрироваться")
            assert page.query_selector("input[name='имя']").is_visible()
            assert page.query_selector("input[name='фамилия']").is_visible()
            assert page.query_selector("input[name='электронная почта']").is_visible()
            assert page.query_selector("text=Заполните поле").is_visible()

def test_tc_02(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-02":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.fill("input[name='имя']", data["inputs"]["имя"])
            page.click("text=Зарегистрироваться")
            assert page.query_selector("input[name='имя']").is_visible()
            assert page.query_selector("text=Убедитесь, что это значение содержит не более 32 символов (сейчас [количество])").is_visible()

def test_tc_03(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-03":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.fill("input[name='фамилия']", data["inputs"]["фамилия"])
            page.click("text=Зарегистрироваться")
            assert page.query_selector("input[name='фамилия']").is_visible()
            assert page.query_selector("text=Убедитесь, что это значение содержит не более 32 символов (сейчас [количество])").is_visible()

def test_tc_04(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-04":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.fill("input[name='электронная почта']", data["inputs"]["электронная почта"])
            page.click("text=Зарегистрироваться")
            assert page.query_selector("input[name='электронная почта']").is_visible()
            assert page.query_selector("text=Пожалуйста, введите корректный адрес электронной почты").is_visible()

def test_tc_05(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-05":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.check("input[name='согласие']")
            page.click("text=Зарегистрироваться")
            assert page.query_selector("input[name='согласие']").is_visible()

def test_tc_06(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-06":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.click("text=Зарегистрироваться через VK")
            assert page.query_selector("text=Открывается страница авторизации в VK").is_visible()

def test_tc_07(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-07":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.click("text=Закрыть")
            assert page.query_selector("text=Зарегистрироваться").is_not_visible()

def test_tc_08(page):
    test_data = load_test_data("test_data.json")
    for data in test_data["test_data"]:
        if data["test_case_id"] == "TC-08":
            page.goto("https://otus.ru")
            page.click("text=Зарегистрироваться")
            page.fill("input[name='имя']", data["inputs"]["имя"])
            page.click("text=Зарегистрироваться")
            assert page.query_selector("text=Происходит безшовный переход в личный кабинет").is_visible()
            assert page.query_selector("text=Имя пользователя отображается в блоке профиля пользователя в верхней части сайта").is_visible()
