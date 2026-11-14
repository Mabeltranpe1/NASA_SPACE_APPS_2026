# Guía de colaboración: git flow

Somos varias personas trabajando en este repositorio, así que todos usamos **git flow**.

## Ramas

| Rama | Para qué sirve | Quién escribe |
|---|---|---|
| `main` | Versión estable y entregable. Solo recibe releases y hotfixes. | Nadie directamente |
| `develop` | Integración: aquí se juntan las features terminadas. | Nadie directamente (vía Pull Request) |
| `feature/<nombre>` | Una tarea o funcionalidad nueva. Sale de `develop`. | Cada persona |
| `bugfix/<nombre>` | Corrección de un error en `develop`. | Cada persona |
| `release/<versión>` | Preparar una entrega (por ejemplo, la entrega final del hackathon). | Coordinador |
| `hotfix/<nombre>` | Corrección urgente sobre `main`. | Coordinador |

> ⚠️ **Nunca hagas commit directo en `main` ni en `develop`.**

## Configuración inicial (una sola vez)

```bash
git clone https://github.com/Mabeltranpe1/NASA_SPACE_APPS_2026.git
cd NASA_SPACE_APPS_2026
git checkout develop
git flow init -d          # acepta los valores por defecto (main / develop)
```

Para instalar git flow:
- Ubuntu/WSL: `sudo apt install git-flow`
- macOS: `brew install git-flow-avh`
- Windows: viene incluido en Git for Windows

## Flujo diario

```bash
# 1. Actualizar develop
git checkout develop
git pull origin develop

# 2. Crear tu rama de trabajo
git flow feature start <nombre-corto>      # por ejemplo: diviner-polo-sur

# 3. Trabajar y hacer commits pequeños
git add <archivos>
git commit -m "feat: descarga de mapas PCP de Diviner"

# 4. Publicar la rama en GitHub
git flow feature publish <nombre-corto>    # la primera vez
git push                                   # las siguientes veces

# 5. Abrir un Pull Request hacia develop en GitHub
gh pr create --base develop
```

Cuando el PR esté aprobado y fusionado, borra tu rama local:
```bash
git checkout develop && git pull
git branch -d feature/<nombre-corto>
```

> Preferimos **Pull Requests** en vez de `git flow feature finish`, para que otra persona revise antes de integrar.

## Mantener tu feature al día

Si `develop` avanzó mientras trabajabas:
```bash
git checkout develop && git pull
git checkout feature/<nombre-corto>
git merge develop
```

## Releases (entregas)

```bash
git flow release start 1.0.0
# ajustes finales, versión, documentación
git flow release finish 1.0.0
git push origin main develop --tags
```

## Convención de commits

Usamos prefijos cortos:

| Prefijo | Uso |
|---|---|
| `feat:` | Funcionalidad o análisis nuevo |
| `fix:` | Corrección |
| `data:` | Scripts de descarga o procesamiento de datos |
| `docs:` | Documentación |
| `viz:` | Mapas y visualizaciones |
| `chore:` | Configuración y mantenimiento |

## Reglas sobre datos

- **No subas datos pesados a git.** `data/raw/` y `data/processed/` están en `.gitignore`.
- Guarda en `src/` o en un notebook el **script o los pasos para descargar** cada dataset, para que cualquiera pueda reproducirlo.
- Anota cada fuente nueva en [RECURSOS.md](RECURSOS.md).
- **Notebooks:** limpia las salidas pesadas antes de hacer commit (`Kernel → Restart & Clear Output`).
