"""
matching_algorithm.py
Algoritmo de similitud entre estudiantes, basado en sus intereses
declarados en el perfil.

Se usa el índice de Jaccard: mide qué tan parecidos son dos conjuntos
comparando su intersección contra su unión.

    Jaccard(A, B) = |A ∩ B| / |A ∪ B|

Resultado entre 0 (ningún interés en común) y 1 (exactamente los
mismos intereses). Es simple, rápido de calcular, y fácil de explicar
— apropiado para un prototipo académico con recursos limitados.

Limitación conocida (ver conversación de alcance/limitaciones): esto
mide superposición de etiquetas declaradas, no compatibilidad real
entre personas.
"""

from dataclasses import dataclass
from typing import Set

# Bonus de puntaje si ambos estudiantes son de la misma facultad.
# Se suma DESPUÉS de calcular Jaccard, no reemplaza el cálculo de intereses.
BONUS_MISMA_FACULTAD = 0.15


@dataclass
class ResultadoSimilitud:
    score: float  # score final (0.0 - 1.15 aprox, ya con bonus de facultad)
    score_intereses: float  # solo la parte de Jaccard (0.0 - 1.0)
    intereses_comunes: Set[str]
    misma_facultad: bool


def calcular_jaccard(intereses_a: Set[str], intereses_b: Set[str]) -> float:
    """
    Calcula el índice de Jaccard entre dos conjuntos de intereses.
    Devuelve 0.0 si ambos conjuntos están vacíos (no hay base para comparar).
    """
    if not intereses_a and not intereses_b:
        return 0.0

    interseccion = intereses_a & intereses_b
    union = intereses_a | intereses_b

    if not union:
        return 0.0

    return len(interseccion) / len(union)


def calcular_similitud(
    intereses_a: Set[str],
    intereses_b: Set[str],
    facultad_a: str = None,
    facultad_b: str = None,
) -> ResultadoSimilitud:
    """
    Calcula el puntaje de compatibilidad entre dos estudiantes.

    El puntaje principal es la similitud de intereses (Jaccard). Si
    ambos pertenecen a la misma facultad, se suma un pequeño bonus
    (no reemplaza el cálculo de intereses, solo lo complementa —
    coincidir en facultad facilita el contacto en la práctica, ej.
    materias o eventos en común).
    """
    score_intereses = calcular_jaccard(intereses_a, intereses_b)
    intereses_comunes = intereses_a & intereses_b

    misma_facultad = (
        facultad_a is not None
        and facultad_b is not None
        and facultad_a == facultad_b
    )

    score = score_intereses + (BONUS_MISMA_FACULTAD if misma_facultad else 0.0)

    return ResultadoSimilitud(
        score=round(score, 4),
        score_intereses=round(score_intereses, 4),
        intereses_comunes=intereses_comunes,
        misma_facultad=misma_facultad,
    )