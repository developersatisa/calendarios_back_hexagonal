# 🧠 Backend Calendarios – Arquitectura Hexagonal

Este repositorio implementa un sistema backend para la gestión de calendarios empresariales, procesos y hitos asociados a clientes, respetando los principios de la **arquitectura hexagonal (puertos y adaptadores)** y **principios SOLID**.

---

## 📦 Estructura de Carpetas

```plaintext
calendarios_back_hexagonal/
│
├── app/
│   ├── domain/                       
│   │   ├── entities/                 
│   │   └── repositories/            
│   │
│   ├── application/                 
│   │   └── use_cases/
│   │       ├── procesos/
│   │       ├── hitos/
│   │       ├── clientes/
│   │       ├── plantilla/
│   │       ├── plantilla_proceso/
│   │       ├── cliente_proceso/
│   │       └── cliente_proceso_hito/
│   │
│   ├── infrastructure/              
│   │   ├── db/
│   │   │   ├── database.py          
│   │   │   ├── models/              
│   │   │   └── repositories/        
│   │   └── api/
│   │       └── v1/
│   │           └── endpoints/       
│   │
│   └── main.py                      
│
├── tests/                           
├── scripts/                         
│   ├── mock_data.py
│   └── test_endpoints.py
│
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## ⚙️ Flujo de una Petición

1. El cliente lanza una petición a un endpoint de FastAPI (`/v1/...`)
2. El endpoint recibe la solicitud, extrae los datos y llama a un **caso de uso**
3. El caso de uso invoca a un repositorio **abstracto**
4. Este es inyectado por su implementación concreta (`*_repository_sql.py`)
5. El repositorio ejecuta operaciones con la BBDD a través del ORM SQLAlchemy
6. El resultado se devuelve hacia el cliente

---

## 🧠 Entidades Disponibles

| Entidad                  | Descripción                                      |
|--------------------------|--------------------------------------------------|
| **Proceso**              | Flujo empresarial recurrente                     |
| **Hito**                 | Evento o tarea específica de un proceso          |
| **Plantilla**            | Configuración base con procesos predefinidos     |
| **Cliente**              | Entidad externa consumida desde otra plataforma |
| **ProcesoHitoMaestro**   | Relación entre procesos e hitos base             |
| **PlantillaProceso**     | Asociación entre plantilla y procesos            |
| **ClienteProceso**       | Asignación de procesos a clientes                |
| **ClienteProcesoHito**   | Hitos derivados del cliente_proceso             |

---

## 🔗 Relaciones entre Tablas

```plaintext
Plantilla ⟷ PlantillaProceso ⟶ Proceso
Proceso ⟷ ProcesoHitoMaestro ⟶ Hito

Cliente ⟶ ClienteProceso ⟶ Proceso
ClienteProceso ⟶ ClienteProcesoHito ⟶ Hito (vía ProcesoHitoMaestro)
```

---

## 📆 Generación de Calendarios por Temporalidad

Este sistema permite crear automáticamente registros de `ClienteProceso` en función de la `temporalidad` y `frecuencia` definidas en un `Proceso` maestro.

---

### 🧠 Diseño aplicado

Se ha implementado el **Patrón Estrategia** para separar la lógica de cada tipo de temporalidad en clases individuales, y un **módulo fábrica** para seleccionar dinámicamente la estrategia adecuada.

Ventajas:
- Abierto a nuevas temporalidades sin romper el código existente (Open/Closed).
- Testeable por unidad.
- Código limpio y mantenible.

---

### 📁 Ubicación del código

La lógica de generación se encuentra en:

```
app/application/services/generadores_temporalidad/
```

Contiene:

- `base_generador.py`: Interfaz base (abstracta).
- `factory.py`: Fábrica para obtener el generador según la temporalidad.
- `generador_mensual.py`: Lógica para temporalidad "mes".
- `generador_semanal.py`: Lógica para "semana".
- `generador_diario.py`: Lógica para "día".
- `generador_quincenal.py`: Cada 15 días.
- `generador_trimestral.py`: Tramos fijos de 3 meses.

---

### 🔁 Temporalidades soportadas

| Temporalidad  | Descripción                         |
|---------------|-------------------------------------|
| `dia`         | Procesos generados cada X días      |
| `semana`      | Procesos generados cada X semanas   |
| `quincena`    | Procesos cada 15 días exactos       |
| `mes`         | Procesos cada X meses               |
| `trimestre`   | Procesos cada 3 meses (fijo)        |

---

### ⚙️ Cómo se usa

Desde el use case:

```python
from app.application.services.generadores_temporalidad.factory import obtener_generador

def generar_calendario_cliente_proceso(...):
    generador = obtener_generador(proceso_maestro.temporalidad)
    return generador.generar(data, proceso_maestro, repo)
```

---

### 🧩 Añadir nuevas temporalidades

1. Crear `generador_mitemporalidad.py` en `generadores_temporalidad/`.
2. Heredar de `GeneradorTemporalidad` e implementar `generar(...)`.
3. Registrar en `factory.py`:

```python
elif temporalidad == "mitemporalidad":
    return GeneradorMiTemporalidad()
```

---

## ✍️ Proceso para Agregar Nuevas Entidades

1. **Dominio**
   - Crear clase en `entities/`
   - Crear interfaz abstracta en `repositories/`

2. **Casos de Uso**
   - Crear funciones específicas en `use_cases/<entidad>/`

3. **Infraestructura**
   - Crear modelo en `models/`
   - Crear repositorio en `repositories/`

4. **API**
   - Crear endpoint en `endpoints/`

5. **Mocks y Test**
   - Agregar mocks en `scripts/mock_data.py`
   - Agregar pruebas en `scripts/test_endpoints.py`

---

## 🛠️ Cambio de Motor de Base de Datos

1. Crear una nueva clase repositorio implementando la interfaz
2. Sustituir la inyección en los endpoints
3. ¡El dominio y casos de uso no se tocan! ✅

---

## 🧪 Scripts Disponibles

| Script                | Descripción                            |
|-----------------------|----------------------------------------|
| `mock_data.py`        | Inserta datos simulados en la BBDD     |
| `test_endpoints.py`   | Ejecuta tests para todos los endpoints |

---

## 🤖 Documentación para Claude Code

Este proyecto incluye un archivo `CLAUDE.md` que proporciona contexto y comandos útiles para instancias de Claude Code que trabajen en este repositorio. Incluye:

- Comandos de desarrollo y Docker
- Arquitectura y patrones de diseño
- Sistema de generación de calendarios
- Configuración de autenticación y SSO
- Estrategias de testing

Consulta `CLAUDE.md` para información detallada sobre el desarrollo en este proyecto.

---

## ✅ Buenas Prácticas Aplicadas

- Arquitectura hexagonal limpia
- Responsabilidad única y principios SOLID
- Separación entre lógica de negocio, aplicación y persistencia
- Fácil testeo, mantenimiento y escalabilidad

---


# 🔐 Autenticación API por API Key + JWT + Refresh Token + SSO

Este proyecto implementa un sistema de autenticación simple y seguro basado en creación de clientes API, generación de claves y uso de JWTs para acceder a rutas protegidas. Además, incluye soporte para **Single Sign-On (SSO)** con Microsoft Azure AD para usuarios de ATISA.

---

## 1️⃣ Crear un nuevo cliente API

**Endpoint:**  
`POST /admin/api-clientes`

**Headers:**
- `X-Admin-API-Key: <CLAVE_SECRETA_ADMIN>`

**Body (JSON):**
```json
{
  "nombre_cliente": "cliente_demo",
  "password": "MiPassword123!"  // Opcional - si no se envía, se genera automáticamente
}
```

**Respuesta:**
```json
{
  "mensaje": "Cliente creado",
  "api_key": "MiPassword123!",
  "cliente": "cliente_demo",
  "password_personalizada": true
}
```

⚠️ **IMPORTANTE:** La `api_key` se muestra **una sola vez**.  
Esta clave sirve como contraseña del cliente. No se almacena en texto plano en la base de datos.

### 🔒 Validación de contraseñas

**Endpoint:**  
`POST /admin/validar-password`

**Headers:**
- `X-Admin-API-Key: <CLAVE_SECRETA_ADMIN>`

**Body (JSON):**
```json
{
  "password": "contraseña_a_validar"
}
```

**Respuesta:**
```json
{
  "valida": false,
  "mensaje": "Contraseña no cumple con los criterios",
  "errores": [
    "La contraseña debe tener al menos 8 caracteres",
    "La contraseña debe contener al menos una letra mayúscula"
  ],
  "criterios": {
    "longitud_minima": 8,
    "requiere_minuscula": true,
    "requiere_mayuscula": true,
    "requiere_numero": true,
    "requiere_caracter_especial": true
  }
}
```

---

## 2️⃣ Obtener tokens (access + refresh)

**Endpoint:**  
`POST /token`

**Headers:**
- `Content-Type: application/x-www-form-urlencoded`

**Body (form-data):**
```
username=cliente_demo
password=KZURpV7R2Fn0L3DKGk8vdHjZyNqUs9kEIxDdSytaz
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 3️⃣ Usar el access token

Una vez con el `access_token`, inclúyelo en la cabecera de cada request:

```http
GET /clientes
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

---

## 4️⃣ Renovar el access token con refresh token

**Endpoint:**  
`POST /refresh-token`

**Headers:**
- `Content-Type: application/json`

**Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

> ⚠️ Si el refresh token ha expirado, se debe solicitar login nuevamente.

---

## 5️⃣ Manejo de errores

Si el token es inválido o ha expirado, se devuelve:

```json
{
  "detail": "Token inválido o expirado"
}
```

Esto permite al cliente frontend detectar el estado de la sesión y redirigir al login o intentar renovar el token.

---

## 🧪 Ejemplo de uso con curl

```bash
# Crear cliente API (admin)
curl -X POST http://localhost:8088/admin/api-clientes \
  -H "x-admin-key: <CLAVE_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"nombre_cliente": "cliente_demo"}'

# Obtener tokens
curl -X POST http://localhost:8088/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=cliente_demo" \
  -d "password=<CLAVE_ENTREGADA>"

# Usar access token
curl http://localhost:8088/clientes \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Renovar access token con refresh token
curl -X POST http://localhost:8088/refresh-token \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<REFRESH_TOKEN>"}'
```

--
docker compose --profile ARC --project-name arc_hex_backend up -d


# Levantar los servicios (modo desatendido)
docker compose up -d

# Ver el estado de los contenedores
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Detener y eliminar los servicios, contenedores, redes y volúmenes
docker compose down --volumes --remove-orphans

---

## 🔑 Single Sign-On (SSO) con Microsoft Azure AD

### 📋 Configuración requerida

Para habilitar SSO, añade estas variables al archivo `.env`:

```bash
# Credenciales de Azure AD
CLIENT_ID=tu-application-id
CLIENT_SECRET=tu-client-secret
TENANT_ID=tu-tenant-id
REDIRECT_URI=http://localhost:8000/sso/callback
```

### 🔄 Flujo de autenticación SSO

#### 1️⃣ Iniciar proceso SSO
```http
GET /sso/login
```

**Respuesta:**
```json
{
  "auth_url": "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?...",
  "message": "Redirige al usuario a esta URL para completar la autenticación"
}
```

#### 2️⃣ Callback después de autenticación
```http
GET /sso/callback?code={codigo_de_azure}
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user_info": {
    "username": "Juan Pérez",
    "email": "juan.perez@atisa.es",
    "id_api_cliente": 1,
    "atisa": true,
    "rol": "admin"
  }
}
```

### 🏢 Usuarios permitidos

El SSO solo permite usuarios con dominios de ATISA:
- `@atisa.es`
- `@atisa-grupo.com`

Los usuarios SSO se asignan automáticamente a `id_api_cliente=1` con rol `admin`.

### ⚠️ SSO opcional

Si las credenciales SSO no están configuradas:
- La aplicación funciona normalmente
- Los endpoints SSO devuelven HTTP 503
- Solo están disponibles los métodos de autenticación tradicionales

---

