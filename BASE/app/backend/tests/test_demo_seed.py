from sqlalchemy import func, select

from app import seeds
from app.database import worker_session
from app.models import (Alerta, Company, Contrato, Documento,
                        EventoCalendario, Sujeto, User)
from app.services.vencimientos import recalcular_documentos


def test_seed_operacional_demo_es_amplio_y_repetible(app_cliente):
    with worker_session(is_admin=True) as db:
        seeds.run(db)
        recalcular_documentos(db)

        empresas = list(db.scalars(select(Company)))
        assert len(empresas) == 16

        def conteos(empresa):
            return (
                db.scalar(select(func.count()).select_from(Contrato).where(
                    Contrato.company_id == empresa.id)),
                db.scalar(select(func.count()).select_from(Sujeto).where(
                    Sujeto.company_id == empresa.id, Sujeto.tipo == "trabajador")),
                db.scalar(select(func.count()).select_from(Sujeto).where(
                    Sujeto.company_id == empresa.id, Sujeto.tipo == "equipo")),
                db.scalar(select(func.count()).select_from(Documento).where(
                    Documento.company_id == empresa.id)),
                db.scalar(select(func.count()).select_from(Alerta).where(
                    Alerta.company_id == empresa.id)),
                db.scalar(select(func.count()).select_from(EventoCalendario).where(
                    EventoCalendario.company_id == empresa.id)),
            )

        conteos_antes = {empresa.id: conteos(empresa) for empresa in empresas}
        for empresa in empresas:
            contratos, personal, equipos, documentos, alertas, eventos = conteos_antes[empresa.id]
            if empresa.nombre == "DEMO SpA":
                assert contratos >= 8
                assert personal >= 30
                assert equipos >= 18
                assert documentos >= 500
            else:
                assert contratos >= 2
                assert personal >= 8
                assert equipos >= 4
                assert documentos >= 100
            assert alertas > 0, empresa.nombre
            assert eventos >= 3, empresa.nombre

        patentes = list(db.scalars(select(Sujeto.patente).where(
            Sujeto.tipo == "equipo")))
        nombres_personal = list(db.scalars(select(Sujeto.nombre).where(
            Sujeto.tipo == "trabajador")))
        nombres_usuarios = list(db.scalars(select(User.nombre).where(
            User.nombre.is_not(None))))

        assert len(patentes) == len(set(patentes))
        assert len(nombres_personal) == len(set(nombres_personal))
        assert len(nombres_usuarios) == len(set(nombres_usuarios))

        seeds.run(db)
        conteos_despues = {empresa.id: conteos(empresa) for empresa in empresas}
        assert conteos_despues == conteos_antes