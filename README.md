# Block PDF Project

Generador local de PDFs por `BLOCKID` a partir de:

- Excel por país.
- KMLs locales por bloque.
- Geoapify Static Maps API para generar mapa callejero con nombres de calles y overlay del bloque.
- Caché para evitar consumir requests nuevamente.
- CLI para pruebas, producción parcial, producción total y faltantes.

## 1. Instalación

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

Copia el archivo de entorno:

```bash
copy .env.example .env
```

Edita `.env`:

```env
GEOAPIFY_API_KEY=tu_api_key
```

## 2. Estructura esperada de datos

```text
data/
  peru/
    input/blocks.xlsx
    kml/BLOCKID.kml
  bolivia/
    input/blocks.xlsx
    kml/BLOCKID.kml
  paraguay/
    input/blocks.xlsx
    kml/BLOCKID.kml
```

El Excel debe tener, como mínimo:

```text
BLOCKID, CITY_PRE, ONAME_PRE, NAME_PRE, STREET_NM_PRE, OTYPE_PRE, STREET_NM, STREET_NO3, REF1, REF2
```

## 3. Comandos principales

Validar entradas:

```bash
python -m src.main validate --country peru
```

Prueba visual sin caché, 10 bloques:

```bash
python -m src.main preview --country peru --sample-size 10
```

Ejecutar todo un país con caché:

```bash
python -m src.main run --country peru
```

Ejecutar primeros 2000:

```bash
python -m src.main run --country peru --offset 0 --limit 2000
```

Ejecutar siguientes 2000:

```bash
python -m src.main run --country peru --offset 2000 --limit 2000
```

Ejecutar solo faltantes:

```bash
python -m src.main run --country peru --only-missing
```

Ejecutar todos los países:

```bash
python -m src.main run --country all
```

Forzar regeneración ignorando caché:

```bash
python -m src.main run --country peru --force
```

Usar lista específica:

```bash
python -m src.main run --country peru --block-ids-file block_ids.txt
```

## 4. Modos

### Preview

- No usa caché.
- No guarda en caché.
- Guarda resultados en `data/<pais>/preview/`.
- Sirve para ajustar estilos, zoom, tabla, tamaño de imagen.

### Run / Producción

- Usa caché.
- Salta mapas y PDFs existentes.
- Guarda resultados en `data/<pais>/output/`.
- Registra manifest y errores en `runs/`.

## 5. Configuración

Los YAML principales están en:

```text
config/base.yaml
config/layout.yaml
config/countries/peru.yaml
config/countries/bolivia.yaml
config/countries/paraguay.yaml
config/profiles/test.yaml
config/profiles/prod.yaml
```

Puedes cambiar labels de tabla, agrupaciones, zoom, estilo, rutas, tamaño de imagen, color del polígono y comportamiento de caché sin tocar código.

## 6. Notas Geoapify

El proveedor implementado usa Geoapify Static Maps API vía POST con GeoJSON para poder incrustar el polígono del KML sobre el mapa base.

Si un KML tiene geometrías muy grandes, el sistema simplifica la geometría según `map.geometry_simplify_tolerance` para evitar requests demasiado pesadas.
