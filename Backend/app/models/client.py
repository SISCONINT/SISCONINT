from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

# tipo_persona
TIPO_FISICA = "FISICA"
TIPO_MORAL = "MORAL"

# forma_pago
FORMA_EFECTIVO = "EFECTIVO"
FORMA_TRANSFERENCIA = "TRANSFERENCIA"

# tipo_nomina
NOMINA_SEMANAL = "SEMANAL"
NOMINA_QUINCENAL = "QUINCENAL"
NOMINA_MENSUAL = "MENSUAL"

# estatus
ESTATUS_ACTIVO = "ACTIVO"
ESTATUS_PAUSADO = "PAUSADO"
ESTATUS_BAJA = "BAJA"

# contacto_cliente.tipo
CONTACTO_PRINCIPAL = "PRINCIPAL"
CONTACTO_PAGOS = "PAGOS"


class Cliente(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_11-16. Expediente fiscal del cliente."""

    __tablename__ = "cliente"

    id = db.Column(BigId, primary_key=True)
    nombre_completo = db.Column(db.String(200), nullable=False)
    rfc = db.Column(db.String(13), nullable=False)
    tipo_persona = db.Column(db.String(6), nullable=False)
    razon_social = db.Column(db.String(250))
    forma_pago = db.Column(db.String(15), nullable=False)
    contador_asignado_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    giro = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(10), nullable=False)
    correo = db.Column(db.String(254), nullable=False)
    codigo_postal = db.Column(db.String(5), nullable=False)
    calle = db.Column(db.String(150), nullable=False)
    no_exterior = db.Column(db.String(20), nullable=False)
    no_interior = db.Column(db.String(20))
    colonia = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(100), nullable=False)
    tiene_trabajadores = db.Column(db.Boolean, nullable=False)
    tipo_nomina = db.Column(db.String(10))
    estatus = db.Column(db.String(10), nullable=False, default=ESTATUS_ACTIVO)
    motivo_baja = db.Column(db.String(300))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    regimenes = db.relationship(
        "ClienteRegimen", back_populates="cliente", cascade="all, delete-orphan", lazy="selectin"
    )
    contactos = db.relationship(
        "ContactoCliente",
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def activo(self) -> bool:
        return self.estatus == ESTATUS_ACTIVO and self.deleted_at is None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre_completo": self.nombre_completo,
            "rfc": self.rfc,
            "tipo_persona": self.tipo_persona,
            "razon_social": self.razon_social,
            "forma_pago": self.forma_pago,
            "contador_asignado_id": self.contador_asignado_id,
            "giro": self.giro,
            "telefono": self.telefono,
            "correo": self.correo,
            "codigo_postal": self.codigo_postal,
            "calle": self.calle,
            "no_exterior": self.no_exterior,
            "no_interior": self.no_interior,
            "colonia": self.colonia,
            "ciudad": self.ciudad,
            "estado": self.estado,
            "tiene_trabajadores": self.tiene_trabajadores,
            "tipo_nomina": self.tipo_nomina,
            "estatus": self.estatus,
            "motivo_baja": self.motivo_baja,
            "regimenes": [r.regimen_clave for r in self.regimenes],
            "contactos": [c.to_dict() for c in self.contactos if c.deleted_at is None],
        }


class RegimenFiscal(db.Model):
    """Catálogo SAT c_RegimenFiscal (tabla semilla, sin soft delete ni timestamps)."""

    __tablename__ = "regimen_fiscal"

    clave = db.Column(db.String(3), primary_key=True)
    descripcion = db.Column(db.String(250), nullable=False)
    aplica_fisica = db.Column(db.Boolean, nullable=False, default=False)
    aplica_moral = db.Column(db.Boolean, nullable=False, default=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)


class ClienteRegimen(db.Model):
    """Relación N:M entre cliente y régimen fiscal."""

    __tablename__ = "cliente_regimen"

    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), primary_key=True)
    regimen_clave = db.Column(db.String(3), db.ForeignKey("regimen_fiscal.clave"), primary_key=True)

    cliente = db.relationship("Cliente", back_populates="regimenes")
    regimen = db.relationship("RegimenFiscal", lazy="joined")


class ContactoCliente(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_11. PRINCIPAL obligatorio; PAGOS opcional con regla 'todo o nada'."""

    __tablename__ = "contacto_cliente"

    id = db.Column(BigId, primary_key=True)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=False, index=True)
    tipo = db.Column(db.String(10), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(10), nullable=False)
    correo = db.Column(db.String(254), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    cliente = db.relationship("Cliente", back_populates="contactos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "nombre_completo": self.nombre_completo,
            "telefono": self.telefono,
            "correo": self.correo,
            "cargo": self.cargo,
        }