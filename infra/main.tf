resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}"
  location = var.location
  tags     = var.tags
}

# Static Web App (plan Free): hospeda el frontend de React en web/.
# El despliegue del código se hace desde GitHub Actions con el token de despliegue.
resource "azurerm_static_web_app" "web" {
  name                = "swa-${var.project_name}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku_tier            = var.static_web_app_sku
  sku_size            = var.static_web_app_sku
  tags                = var.tags
}
