variable "subscription_id" {
  description = "ID de la suscripción de Azure (az account show --query id -o tsv)"
  type        = string
}

variable "project_name" {
  description = "Nombre corto del proyecto, se usa en los nombres de los recursos"
  type        = string
  default     = "nasa-analogs"
}

variable "location" {
  description = "Región de Azure. Static Web Apps solo está en: westus2, centralus, eastus2, westeurope, eastasia"
  type        = string
  default     = "eastus2"
}

variable "static_web_app_sku" {
  description = "Plan de Static Web Apps. Debe ser Free salvo aprobación explícita para usar Standard (de pago)."
  type        = string
  default     = "Free"

  validation {
    condition     = contains(["Free", "Standard"], var.static_web_app_sku)
    error_message = "El plan debe ser Free o Standard."
  }
}

variable "tags" {
  description = "Etiquetas comunes para todos los recursos"
  type        = map(string)
  default = {
    project = "nasa-space-apps-2026"
    managed = "terraform"
  }
}
