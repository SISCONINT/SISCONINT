"""Pruebas de humo de los endpoints MVP de catálogo, obligaciones, minutas, tarifas,
calendario, reportes y plantillas."""
from datetime import timedelta
from io import BytesIO

from app.core.datetime_utils import today_mx
from tests.time_helpers import crear_categoria, crear_cliente, crear_tarea


def test_mvp_smoke(app, client, make_user, auth_headers):
    dueno = make_user("dueno.smoke@despacho.com", "DUENO", nombre="Dueño Smoke")
    contador = make_user("contador.smoke@despacho.com", "CONTADOR", nombre="Contador Smoke")
    cliente = crear_cliente(contador, "Cliente Smoke", "XSMK010101000")
    categoria = crear_categoria("Smoke")
    tarea = crear_tarea(
        titulo="Tarea smoke",
        cliente=cliente,
        categoria=categoria,
        asignado=contador,
        creador=dueno,
        fecha_limite=today_mx() + timedelta(days=3),
    )
    headers = auth_headers(dueno)

    res = client.get("/api/v1/users/options?rol=CONTADOR", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == contador.id for item in res.get_json()["data"])

    res = client.get("/api/v1/clients/options", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == cliente.id for item in res.get_json()["data"])

    res = client.get("/api/v1/tasks/options?incluir_completadas=true", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == tarea.id for item in res.get_json()["data"])

    res = client.post("/api/v1/catalog", headers=headers, json={"nombre": "Raíz smoke"})
    assert res.status_code == 201, res.get_json()
    raiz = res.get_json()["data"]
    res = client.post(
        "/api/v1/catalog",
        headers=headers,
        json={"nombre": "Sub smoke", "padre_id": raiz["id"]},
    )
    assert res.status_code == 201, res.get_json()
    sub = res.get_json()["data"]
    res = client.put(
        f"/api/v1/catalog/{sub['id']}",
        headers=headers,
        json={"nombre": "Sub smoke editada", "orden": 2, "activa": True},
    )
    assert res.status_code == 200, res.get_json()
    res = client.post(f"/api/v1/catalog/{raiz['id']}/deactivate", headers=headers)
    assert res.status_code == 200, res.get_json()

    res = client.post(
        "/api/v1/obligations",
        headers=headers,
        json={
            "cliente_id": cliente.id,
            "categoria_id": categoria.id,
            "responsable_id": contador.id,
            "periodicidad": "MENSUAL",
            "dia_vencimiento": 17,
            "fecha_inicio": today_mx().isoformat(),
            "prioridad": "ALTA",
        },
    )
    assert res.status_code == 201, res.get_json()
    obligacion = res.get_json()["data"]
    assert obligacion["dia_vencimiento"] == 17
    assert obligacion["responsable_id"] == contador.id
    assert "nombre" not in obligacion
    res = client.get("/api/v1/obligations", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == obligacion["id"] for item in res.get_json()["data"])
    res = client.put(
        f"/api/v1/obligations/{obligacion['id']}",
        headers=headers,
        json={
            "cliente_id": cliente.id,
            "categoria_id": categoria.id,
            "responsable_id": contador.id,
            "periodicidad": "BIMESTRAL",
            "dia_vencimiento": 20,
            "fecha_inicio": today_mx().isoformat(),
            "prioridad": "MEDIA",
            "activa": True,
        },
    )
    assert res.status_code == 200, res.get_json()
    assert res.get_json()["data"]["periodicidad"] == "BIMESTRAL"
    res = client.post(f"/api/v1/obligations/{obligacion['id']}/deactivate", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert res.get_json()["data"]["activa"] is False

    contenido = b"%PDF-1.4 minuta de prueba"
    res = client.post(
        "/api/v1/minutes",
        headers=headers,
        data={
            "tipo": "CLIENTE",
            "cliente_id": str(cliente.id),
            "tarea_id": str(tarea.id),
            "titulo": "Minuta smoke",
            "fecha_reunion": today_mx().isoformat(),
            "observaciones": "Acuerdos de la reunión",
            "archivo": (BytesIO(contenido), "minuta.pdf"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 201, res.get_json()
    minuta = res.get_json()["data"]
    assert minuta["archivo_nombre"] == "minuta.pdf"
    assert minuta["archivo_bytes"] == len(contenido)
    res = client.get("/api/v1/minutes", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == minuta["id"] for item in res.get_json()["data"])
    res = client.get(f"/api/v1/minutes/{minuta['id']}/download", headers=headers)
    assert res.status_code == 200
    assert res.data == contenido
    res = client.put(
        f"/api/v1/minutes/{minuta['id']}",
        headers=headers,
        data={
            "tipo": "CLIENTE",
            "cliente_id": str(cliente.id),
            "tarea_id": str(tarea.id),
            "titulo": "Minuta smoke editada",
            "fecha_reunion": today_mx().isoformat(),
            "observaciones": "Acuerdo actualizado.",
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 200, res.get_json()
    assert res.get_json()["data"]["titulo"] == "Minuta smoke editada"
    res = client.delete(f"/api/v1/minutes/{minuta['id']}", headers=headers)
    assert res.status_code == 200, res.get_json()

    res = client.put(
        "/api/v1/rates/JUNIOR",
        headers=headers,
        json={"monto_hora_mxn": 450.5},
    )
    assert res.status_code == 200, res.get_json()
    assert res.get_json()["data"]["nivel"] == "JUNIOR"
    res = client.get("/api/v1/rates", headers=headers)
    assert res.status_code == 200, res.get_json()
    row = next(item for item in res.get_json()["data"] if item["nivel"] == "JUNIOR")
    assert row["monto_hora_mxn"] == 450.5
    assert row["vigente"] is True

    res = client.get(
        "/api/v1/calendar",
        headers=headers,
        query_string={
            "fecha_desde": today_mx().isoformat(),
            "fecha_hasta": (today_mx() + timedelta(days=15)).isoformat(),
        },
    )
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == tarea.id for item in res.get_json()["data"]["eventos"])

    res = client.get("/api/v1/reports/summary", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert "tareas_completadas" in res.get_json()["data"]
    assert "generado_en" in res.get_json()["data"]

    res = client.post(
        "/api/v1/templates",
        headers=headers,
        json={
            "clave": "ASIGNACION",
            "asunto": "Asunto smoke",
            "cuerpo": "Cuerpo smoke",
        },
    )
    assert res.status_code == 201, res.get_json()
    plantilla = res.get_json()["data"]
    assert plantilla["asunto_original"] == "Asunto smoke"
    res = client.put(
        f"/api/v1/templates/{plantilla['id']}",
        headers=headers,
        json={"asunto": "Asunto editado", "cuerpo": "Cuerpo editado"},
    )
    assert res.status_code == 200, res.get_json()
    assert res.get_json()["data"]["asunto"] == "Asunto editado"
    res = client.get("/api/v1/templates", headers=headers)
    assert res.status_code == 200, res.get_json()
    assert any(item["id"] == plantilla["id"] for item in res.get_json()["data"])
