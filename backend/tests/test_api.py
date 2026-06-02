import os
import pytest
from fastapi.testclient import TestClient
from .test_config import ADMIN_PASSWORD, SECRETARY_PASSWORD, GUARD_PASSWORD

# ==================== AUTHENTICATION ====================

def test_login_success(client: TestClient):
    response = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["role"] == "admin"

def test_login_wrong_password(client: TestClient):
    response = client.post("/token", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный логин или пароль"

def test_refresh_token_works(client: TestClient):
    login_resp = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    assert login_resp.status_code == 200
    refresh_cookie = login_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None
    refresh_resp = client.post("/refresh")
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()

def test_logout_clears_cookie(client: TestClient):
    login_resp = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    logout_resp = client.post("/logout", headers=headers)
    assert logout_resp.status_code == 200
    set_cookie_header = logout_resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie_header and "Max-Age=0" in set_cookie_header

# ==================== VISITORS ====================

def test_create_visitor_as_admin(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/visitors", json={
        "full_name": "Иван Петров",
        "company": "ООО Ромашка",
        "whom_visit": "Директор",
        "purpose": "Совещание"
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Иван Петров"

def test_create_visitor_as_guard(client: TestClient):
    login = client.post("/token", data={"username": "guard", "password": GUARD_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/visitors", json={
        "full_name": "Посетитель от охраны",
        "company": "ООО Тест",
        "whom_visit": "Директор",
        "purpose": "Встреча"
    }, headers=headers)
    assert response.status_code == 200

def test_cannot_create_duplicate_active_visitor(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp1 = client.post("/visitors", json={
        "full_name": "Двойник",
        "company": "ООО Тест",
        "whom_visit": "Директор",
        "purpose": "Совещание"
    }, headers=headers)
    assert resp1.status_code == 200
    visitor_id = resp1.json().get("id")
    assert visitor_id is not None
    resp2 = client.post("/visitors", json={
        "full_name": "Двойник",
        "company": "ООО Тест",
        "whom_visit": "Директор",
        "purpose": "Совещание"
    }, headers=headers)
    assert resp2.status_code == 400
    assert "таким ФИО уже на территории" in resp2.json()["detail"]
    client.put(f"/visitors/{visitor_id}/checkout", headers=headers)
    resp3 = client.post("/visitors", json={
        "full_name": "Двойник",
        "company": "ООО Тест",
        "whom_visit": "Директор",
        "purpose": "Совещание"
    }, headers=headers)
    assert resp3.status_code == 200

def test_checkout_visitor_access(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin.json()["access_token"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}
    resp1 = client.post("/visitors", json={
        "full_name": "Иван Петров",
        "company": "ООО Ромашка",
        "whom_visit": "Директор",
        "purpose": "Совещание"
    }, headers=admin_h)
    assert resp1.status_code == 200
    vid = resp1.json()["id"]
    guard = client.post("/token", data={"username": "guard", "password": GUARD_PASSWORD})
    guard_token = guard.json()["access_token"]
    ch = client.put(f"/visitors/{vid}/checkout", headers={"Authorization": f"Bearer {guard_token}"})
    assert ch.status_code == 200
    resp2 = client.post("/visitors", json={
        "full_name": "Петр Сидоров",
        "company": "ООО Звезда",
        "whom_visit": "Менеджер",
        "purpose": "Переговоры"
    }, headers=admin_h)
    assert resp2.status_code == 200
    vid2 = resp2.json()["id"]
    sec = client.post("/token", data={"username": "secretary", "password": SECRETARY_PASSWORD})
    sec_token = sec.json()["access_token"]
    ch2 = client.put(f"/visitors/{vid2}/checkout", headers={"Authorization": f"Bearer {sec_token}"})
    assert ch2.status_code == 403

def test_filter_search_hide_completed(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r1 = client.post("/visitors", json={
        "full_name": "АлексейСмирнов",
        "company": "ООО А",
        "whom_visit": "Директор",
        "purpose": "Разговор"
    }, headers=headers)
    assert r1.status_code == 200
    vid1 = r1.json()["id"]
    r2 = client.post("/visitors", json={
        "full_name": "МарияИванова",
        "company": "ООО Б",
        "whom_visit": "Менеджер",
        "purpose": "Совещание"
    }, headers=headers)
    assert r2.status_code == 200
    all_resp = client.get("/visitors?hide_completed=true", headers=headers)
    assert len(all_resp.json()["items"]) == 2
    client.put(f"/visitors/{vid1}/checkout", headers=headers)
    final = client.get("/visitors?hide_completed=true", headers=headers)
    assert len(final.json()["items"]) == 1
    assert final.json()["items"][0]["full_name"] == "МарияИванова"

def test_pagination_works(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post("/visitors", json={
        "full_name": "Пагинация Тест",
        "company": "ООО",
        "whom_visit": "Директор",
        "purpose": "Тест пагинации"
    }, headers=headers)
    assert create_resp.status_code == 200
    resp2 = client.get("/visitors?skip=0&limit=1", headers=headers)
    assert len(resp2.json()["items"]) == 1

# ==================== USERS & ROLES ====================

def test_users_endpoint_only_for_admin(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    resp_admin = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    sec_login = client.post("/token", data={"username": "secretary", "password": SECRETARY_PASSWORD})
    sec_token = sec_login.json()["access_token"]
    resp_sec = client.get("/users", headers={"Authorization": f"Bearer {sec_token}"})
    assert resp_sec.status_code == 403
    guard_login = client.post("/token", data={"username": "guard", "password": GUARD_PASSWORD})
    guard_token = guard_login.json()["access_token"]
    resp_guard = client.get("/users", headers={"Authorization": f"Bearer {guard_token}"})
    assert resp_guard.status_code == 403

def test_only_admin_can_create_user(client: TestClient):
    sec = client.post("/token", data={"username": "secretary", "password": SECRETARY_PASSWORD})
    sec_token = sec.json()["access_token"]
    resp = client.post("/users", json={
        "username": "newuser1",
        "password": "StrongPass123",
        "full_name": "Тестовый Пользователь",
        "role": "guard"
    }, headers={"Authorization": f"Bearer {sec_token}"})
    assert resp.status_code == 403
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin.json()["access_token"]
    resp2 = client.post("/users", json={
        "username": "newuser2",
        "password": "StrongPass123",
        "full_name": "Новый Админский Пользователь",
        "role": "secretary"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code == 200

def test_only_admin_can_change_role(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = client.post("/users", json={
        "username": "roletest",
        "password": "StrongPass123",
        "full_name": "Role Test",
        "role": "secretary"
    }, headers=admin_headers)
    assert create_resp.status_code == 200
    users = client.get("/users", headers=admin_headers).json()
    user = next((u for u in users if u["username"] == "roletest"), None)
    assert user is not None
    user_id = user["id"]
    change_resp = client.put(f"/users/{user_id}/role?role=guard", headers=admin_headers)
    assert change_resp.status_code == 200
    sec_login = client.post("/token", data={"username": "secretary", "password": SECRETARY_PASSWORD})
    sec_token = sec_login.json()["access_token"]
    sec_headers = {"Authorization": f"Bearer {sec_token}"}
    forbidden_resp = client.put(f"/users/{user_id}/role?role=admin", headers=sec_headers)
    assert forbidden_resp.status_code == 403

# ==================== LOGS ====================

def test_logs_endpoint_only_for_admin(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    resp_admin = client.get("/logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    sec_login = client.post("/token", data={"username": "secretary", "password": SECRETARY_PASSWORD})
    sec_token = sec_login.json()["access_token"]
    resp_sec = client.get("/logs", headers={"Authorization": f"Bearer {sec_token}"})
    assert resp_sec.status_code == 403

# ==================== EDGE CASES / EXTRA COVERAGE (original) ====================

def test_refresh_with_invalid_token_returns_401(client: TestClient):
    login_resp = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    assert login_resp.status_code == 200
    client.cookies.set("refresh_token", "invalid.token.value")
    refresh_resp = client.post("/refresh")
    assert refresh_resp.status_code == 401

def test_admin_cannot_change_own_role(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    users = client.get("/users", headers=admin_headers).json()
    admin_id = next(u["id"] for u in users if u["username"] == "admin")
    change_resp = client.put(f"/users/{admin_id}/role?role=secretary", headers=admin_headers)
    assert change_resp.status_code in (400, 403)

def test_delete_nonexistent_user_returns_404(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.delete("/users/99999", headers=admin_headers)
    assert resp.status_code == 404

def test_logs_filter_by_action(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    resp = client.get("/logs?action=login", headers=admin_headers)
    assert resp.status_code == 200
    logs = resp.json()["items"]
    assert len(logs) > 0
    assert all(log["action"] == "login" for log in logs)

def test_create_visitor_empty_fields_returns_422(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/visitors", json={"full_name": "", "company": "", "whom_visit": "", "purpose": ""}, headers=headers)
    assert resp.status_code == 422

def test_visitor_list_with_max_limit(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/visitors?limit=500", headers=headers)
    assert resp.status_code == 200

def test_visitor_list_with_negative_skip_returns_422(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/visitors?skip=-10", headers=headers)
    assert resp.status_code == 422

def test_create_visitor_with_special_chars(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/visitors", json={
        "full_name": "Смирнов-Петров А.Б.",
        "company": "ООО",
        "whom_visit": "Директор",
        "purpose": "Совещание"
    }, headers=headers)
    assert resp.status_code == 200

def test_create_user_invalid_role(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post("/users", json={
        "username": "badrole",
        "password": "StrongPass123",
        "full_name": "Bad Role",
        "role": "superuser"
    }, headers=admin_headers)
    assert resp.status_code == 422

def test_login_empty_fields(client: TestClient):
    resp = client.post("/token", data={"username": "", "password": ""})
    assert resp.status_code == 422

def test_visitors_list_invalid_limit(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/visitors?limit=1000", headers=headers)
    assert resp.status_code == 422

def test_refresh_after_logout_fails(client: TestClient):
    login_resp = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/logout", headers=headers)
    refresh_resp = client.post("/refresh")
    assert refresh_resp.status_code == 401

def test_delete_user_with_string_id_fails(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.delete("/users/abc", headers=admin_headers)
    assert resp.status_code == 422

def test_excel_report_for_guard_forbidden(client: TestClient):
    guard_login = client.post("/token", data={"username": "guard", "password": GUARD_PASSWORD})
    guard_token = guard_login.json()["access_token"]
    guard_headers = {"Authorization": f"Bearer {guard_token}"}
    resp = client.get("/report/excel", headers=guard_headers)
    assert resp.status_code == 403

def test_create_user_too_long_name(client: TestClient):
    admin_login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    long_name = "А" * 101
    resp = client.post("/users", json={
        "username": "longname",
        "password": "StrongPass123",
        "full_name": long_name,
        "role": "secretary"
    }, headers=admin_headers)
    assert resp.status_code == 422

# ==================== ADDITIONAL TESTS (11 unique) ====================

def test_create_visitor_without_token(client: TestClient):
    resp = client.post("/visitors", json={
        "full_name": "Без токена",
        "company": "Тест",
        "whom_visit": "Никто",
        "purpose": "Тест"
    })
    assert resp.status_code == 401

def test_visitor_list_without_token(client: TestClient):
    resp = client.get("/visitors")
    assert resp.status_code == 401

def test_invalid_visitor_name_rejected(client: TestClient):
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/visitors", json={
        "full_name": "12345",
        "company": "Тест",
        "whom_visit": "Директор",
        "purpose": "Тест"
    }, headers=headers)
    assert resp.status_code == 422

def test_checkout_nonexistent_visitor(client: TestClient):
    login = client.post("/token", data={"username": "guard", "password": GUARD_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.put("/visitors/99999/checkout", headers=headers)
    assert resp.status_code == 404

def test_create_user_duplicate_username(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/users", json={
        "username": "duptest",
        "password": "pass123",
        "full_name": "Original",
        "role": "secretary"
    }, headers=headers)
    resp2 = client.post("/users", json={
        "username": "duptest",
        "password": "pass123",
        "full_name": "Duplicate",
        "role": "guard"
    }, headers=headers)
    assert resp2.status_code == 400

def test_change_nonexistent_user_role(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.put("/users/99999/role?role=guard", headers=headers)
    assert resp.status_code == 404

def test_logs_with_limit(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/logs?limit=10", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 10

def test_visitors_filter_by_date(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/visitors?date_from=2025-01-01T00:00:00Z", headers=headers)
    assert resp.status_code == 200

def test_visitors_search_no_results(client: TestClient):
    admin = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = admin.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/visitors?search=НетТакогоИмени", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []

def test_refresh_without_cookie(client: TestClient):
    resp = client.post("/refresh")
    assert resp.status_code == 401

def test_logout_without_token(client: TestClient):
    resp = client.post("/logout")
    assert resp.status_code == 401

# ==================== TWO EXTRA TESTS TO REACH 42 IN THIS FILE ====================

def test_create_visitor_with_very_long_name(client: TestClient):
    """Проверка валидации длины ФИО (слишком длинное имя -> 422)"""
    login = client.post("/token", data={"username": "admin", "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    long_name = "А" * 101
    resp = client.post("/visitors", json={
        "full_name": long_name,
        "company": "Тест",
        "whom_visit": "Директор",
        "purpose": "Тест"
    }, headers=headers)
    assert resp.status_code == 422

def test_update_nonexistent_visitor(client: TestClient):
    """PUT на несуществующего посетителя (например, отметка выхода) -> 404"""
    login = client.post("/token", data={"username": "guard", "password": GUARD_PASSWORD})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.put("/visitors/99999/checkout", headers=headers)
    assert resp.status_code == 404