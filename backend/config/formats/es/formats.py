"""Sobrescribe el formato numérico por defecto del idioma español, que usa
coma decimal (5,30). El resto de la aplicación — JS, los mensajes de
confirmación, los DecimalField de los formularios (localize=False) — usa
punto decimal; esto evita que las plantillas muestren un formato distinto
según de dónde venga el número."""

DECIMAL_SEPARATOR = "."
THOUSAND_SEPARATOR = ","
NUMBER_GROUPING = 3
