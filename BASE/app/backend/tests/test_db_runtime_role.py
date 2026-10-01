"""PT-03: privilegios PostgreSQL reales, usando exclusivamente la BD efimera."""
import pytest
from sqlalchemy import create_engine, event

from app import database
from app.config import settings


def test_rol_aplicacion_aceptado(esquema):
    motor = create_engine(esquema)
    try:
        with motor.connect() as conexion:
            database.validate_runtime_role(conexion.connection.driver_connection)
    finally:
        motor.dispose()


def test_superusuario_rechazado(motor_admin):
    with motor_admin.connect() as conexion:
        with pytest.raises(database.UnsafeDatabaseRole):
            database.validate_runtime_role(conexion.connection.driver_connection)


@pytest.mark.parametrize("privilegio", ["BYPASSRLS", "CREATEROLE", "CREATEDB"])
def test_privilegios_administrativos_rechazados(esquema, motor_admin, privilegio):
    # Los cambios de rol se revierten siempre en la BD de prueba.
    with motor_admin.begin() as conexion:
        conexion.exec_driver_sql(f"ALTER ROLE acredittia_app {privilegio}")
    motor = create_engine(esquema)
    try:
        with motor.connect() as conexion:
            with pytest.raises(database.UnsafeDatabaseRole):
                database.validate_runtime_role(conexion.connection.driver_connection)
    finally:
        motor.dispose()
        with motor_admin.begin() as conexion:
            conexion.exec_driver_sql(f"ALTER ROLE acredittia_app NO{privilegio}")


def test_propietario_rechazado(esquema, motor_admin):
    with motor_admin.begin() as conexion:
        conexion.exec_driver_sql("CREATE TABLE public.prueba_propietario (id integer)")
        conexion.exec_driver_sql("ALTER TABLE public.prueba_propietario OWNER TO acredittia_app")
    motor = create_engine(esquema)
    try:
        with motor.connect() as conexion:
            with pytest.raises(database.UnsafeDatabaseRole):
                database.validate_runtime_role(conexion.connection.driver_connection)
    finally:
        motor.dispose()
        with motor_admin.begin() as conexion:
            conexion.exec_driver_sql("DROP TABLE public.prueba_propietario")


def test_conexion_produccion_bloqueada(monkeypatch, motor_admin):
    monkeypatch.setattr(settings, "app_env", "production")
    motor = create_engine(motor_admin.url)
    event.listen(motor, "connect", database._validate_production_role)
    try:
        with pytest.raises(database.UnsafeDatabaseRole):
            with motor.connect():
                pytest.fail("No debe entregar una conexion privilegiada")
    finally:
        motor.dispose()
