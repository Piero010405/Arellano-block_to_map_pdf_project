# Comandos de operación

## Validación

```bash
python -m src.main validate --country peru
python -m src.main validate --country bolivia
python -m src.main validate --country paraguay
python -m src.main validate --country all
```

## Pruebas visuales sin caché

```bash
python -m src.main preview --country peru --sample-size 10
python -m src.main preview --country bolivia --sample-size 10
python -m src.main preview --country paraguay --sample-size 10
```

## Prueba sin consumir Geoapify

Genera mapas mock para validar que el Excel, KML y PDF funcionan:

```bash
python -m src.main debug --country peru --sample-size 3
```

## Producción por país

```bash
python -m src.main run --country peru
python -m src.main run --country bolivia
python -m src.main run --country paraguay
```

## Producción por lotes

Primeros 2000:

```bash
python -m src.main run --country peru --offset 0 --limit 2000
```

Siguientes 2000:

```bash
python -m src.main run --country peru --offset 2000 --limit 2000
```

## Solo faltantes

```bash
python -m src.main run --country peru --only-missing
```

## Forzar regeneración

```bash
python -m src.main run --country peru --force
```

## Ejecutar una lista específica

```bash
python -m src.main run --country peru --block-ids-file block_ids.txt
```

## Ejecutar todos los países

```bash
python -m src.main run --country all
```
