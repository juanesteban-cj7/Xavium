"""
search_engine.py
Lógica de búsqueda y filtrado de estudiantes.

Combina filtros explícitos (facultad, texto de nombre) con el
algoritmo de similitud de intereses (matching_algorithm.py) para
ordenar los resultados por compatibilidad.

Solo se muestran cuentas con estado_cuenta = ACTIVO (verificadas),
y nunca al propio estudiante que realiza la búsqueda.
"""

from dataclasses import dataclass
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from database.models import EstadoCuenta, Usuario
from matching.matching_algorithm import calcular_similitud
from security.input_validation import sanitize_text

# Límite por defecto de resultados devueltos, para no sobrecargar la GUI
# ni la base de datos gratuita con consultas/():renderizados enormes.
LIMITE_RESULTADOS_DEFECTO = 30


@dataclass
class ResultadoBusqueda:
    usuario_id: str
    nombre: str
    facultad: str
    edad: int
    intereses: List[str]
    intereses_comunes: List[str]
    score: float
    misma_facultad: bool


def _obtener_intereses_usuario_actual(session_db: Session, usuario_id: str) -> Set[str]:
    usuario = session_db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        return set()
    return {interes.nombre for interes in usuario.intereses}


def buscar_estudiantes(
    session_db: Session,
    usuario_id_actual: str,
    facultad_filtro: Optional[str] = None,
    texto_busqueda: Optional[str] = None,
    solo_con_intereses_comunes: bool = False,
    limite: int = LIMITE_RESULTADOS_DEFECTO,
) -> List[ResultadoBusqueda]:
    """
    Busca y ordena estudiantes activos por compatibilidad con el
    estudiante que realiza la búsqueda.

    - facultad_filtro: si se especifica, solo devuelve estudiantes de
      esa facultad.
    - texto_busqueda: si se especifica, filtra por coincidencia parcial
      en el nombre (búsqueda simple, sin distinguir mayúsculas).
    - solo_con_intereses_comunes: si True, excluye resultados con 0
      intereses en común (útil para "encuentra afines", no para
      "explora todos los de mi facultad").
    - limite: máximo de resultados a devolver (ya ordenados por score).
    """
    intereses_propios = _obtener_intereses_usuario_actual(session_db, usuario_id_actual)

    usuario_actual = (
        session_db.query(Usuario).filter(Usuario.id == usuario_id_actual).first()
    )
    facultad_propia = (
        usuario_actual.facultad.nombre
        if usuario_actual and usuario_actual.facultad
        else None
    )

    query = session_db.query(Usuario).filter(
        Usuario.id != usuario_id_actual,
        Usuario.estado_cuenta == EstadoCuenta.ACTIVO,
    )

    if facultad_filtro:
        facultad_filtro_limpia = sanitize_text(facultad_filtro, max_length=150)
        query = query.join(Usuario.facultad).filter(
            Usuario.facultad.has(nombre=facultad_filtro_limpia)
        )

    if texto_busqueda:
        texto_limpio = sanitize_text(texto_busqueda, max_length=150)
        query = query.filter(Usuario.nombre.ilike(f"%{texto_limpio}%"))

    candidatos = query.all()

    resultados: List[ResultadoBusqueda] = []
    for candidato in candidatos:
        intereses_candidato = {interes.nombre for interes in candidato.intereses}
        facultad_candidato = (
            candidato.facultad.nombre if candidato.facultad else None
        )

        similitud = calcular_similitud(
            intereses_propios,
            intereses_candidato,
            facultad_a=facultad_propia,
            facultad_b=facultad_candidato,
        )

        if solo_con_intereses_comunes and similitud.score_intereses <= 0:
            continue

        resultados.append(
            ResultadoBusqueda(
                usuario_id=candidato.id,
                nombre=candidato.nombre,
                facultad=facultad_candidato or "",
                edad=candidato.edad,
                intereses=sorted(intereses_candidato),
                intereses_comunes=sorted(similitud.intereses_comunes),
                score=similitud.score,
                misma_facultad=similitud.misma_facultad,
            )
        )

    # Orden descendente por score; a igual score, alfabético por nombre
    # para que el resultado sea determinista y no "salte" entre búsquedas.
    resultados.sort(key=lambda r: (-r.score, r.nombre.lower()))

    return resultados[:limite]


def obtener_facultades_disponibles(session_db: Session) -> List[str]:
    """Reexportado por conveniencia para poblar un filtro en la GUI."""
    from profile.profile_manager import list_facultades

    return list_facultades(session_db)