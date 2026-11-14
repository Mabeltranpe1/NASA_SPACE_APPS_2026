# Infraestructura (Terraform + Azure)

Toda la infraestructura se gestiona con Terraform. **Regla del proyecto: solo planes gratuitos.** Cualquier recurso de pago se consulta antes de agregarlo.

## Recursos

| Recurso | Nombre | Plan | Costo |
|---|---|---|---|
| Resource Group | `rg-nasa-analogs` | — | Gratis |
| Static Web App | `swa-nasa-analogs` | **Free** | Gratis (100 GB/mes de ancho de banda, 3 entornos de vista previa) |

## Requisitos

- [Terraform](https://developer.hashicorp.com/terraform/install) 1.9 o superior
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) con sesión iniciada (`az login`)

## Uso

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# edita terraform.tfvars con: az account show --query id -o tsv

terraform init
terraform plan          # revisar qué se va a crear
terraform apply         # crear los recursos

terraform output static_web_app_url
terraform output -raw static_web_app_deployment_token   # para GitHub
```

## Conectar el despliegue con GitHub

El workflow [`.github/workflows/deploy-web.yml`](../.github/workflows/deploy-web.yml) compila `web/` y lo publica:
- **Push a `main`** → producción.
- **Pull Requests hacia `develop` o `main`** → entorno de vista previa con su propia URL.

En GitHub, en *Settings → Secrets and variables → Actions*, crea este secret:

| Secret | Valor |
|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | `terraform output -raw static_web_app_deployment_token` |

Con `gh` (requiere permisos de admin en el repo):
```bash
terraform output -raw static_web_app_deployment_token | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN
```

## Estado de Terraform

Por ahora el estado (`terraform.tfstate`) es **local** y no se sube a git. Solo una persona debe aplicar cambios de infraestructura. Si varias personas necesitan hacerlo, migraremos el estado a un Storage Account de Azure. Eso tiene un costo mínimo, así que se consultará antes.
