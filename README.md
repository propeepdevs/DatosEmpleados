# PROPEEP – Portal del Empleado (RRHH)

Aplicación Flask para recolección y actualización de datos del empleado.

## Requisitos

- Python 3.8+
- SQL Server con ODBC Driver 17 (o 18)
- Base de datos: `dbformularios` en `xxxx.servidor`

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar

```bash
python app.py
```

Acceder en: http://localhost:5000

## Tablas SQL requeridas

```sql
-- Crear esquema
CREATE SCHEMA rrhh;

-- Tabla DatosEmpleados
CREATE TABLE rrhh.DatosEmpleados (
    Id                 INT IDENTITY(1,1) PRIMARY KEY,
    Cedula             NVARCHAR(13)  NOT NULL,
    Nombre             NVARCHAR(100) NOT NULL,
    Sexo               NVARCHAR(1)   NOT NULL,
    EstadoCivil        NVARCHAR(20)  NULL,
    TelefonoMovil      NVARCHAR(15)  NULL,
    TelefonoFijo       NVARCHAR(15)  NULL,
    TelefonoFlota      NVARCHAR(15)  NULL,
    ContactoEmergencia NVARCHAR(30)  NULL,
    TelefonoEmergencia NVARCHAR(30)  NULL,
    Departamento       NVARCHAR(50)  NULL,
    Cargo              NVARCHAR(30)  NULL,
    NivelAcademico     NVARCHAR(30)  NULL,
    ProfesionOficio    NVARCHAR(30)  NULL,
    Provincia          NVARCHAR(30)  NULL,
    Municipio          NVARCHAR(30)  NULL,
    Direccion          NVARCHAR(100) NULL,
    Sector             NVARCHAR(100) NULL,
    Estatus            INT           NULL DEFAULT 1,
    FechaRegistro      DATETIME      NOT NULL DEFAULT GETDATE(),
    RegistradoPor      NVARCHAR(50)  NULL,
    ModificadoPor      NVARCHAR(50)  NULL,
    FechaModificado    DATETIME      NOT NULL DEFAULT GETDATE()
);

-- Tabla DatosFamiliares
CREATE TABLE rrhh.DatosFamiliares (
    Id              INT IDENTITY(1,1) PRIMARY KEY,
    IdDatosEmpleado INT           NOT NULL REFERENCES rrhh.DatosEmpleados(Id),
    Cedula          NVARCHAR(13)  NOT NULL,
    Nombre          NVARCHAR(100) NOT NULL,
    Sexo            NVARCHAR(1)   NOT NULL,
    FechaNacimiento DATE          NULL,
    Edad            INT           NULL,
    Parentesco      NVARCHAR(15)  NULL,
    Estudia         BIT           NOT NULL DEFAULT 0,
    TipoEstudio     NVARCHAR(15)  NULL,
    Documento1      NVARCHAR(255) NULL,
    Documento2      NVARCHAR(255) NULL,
    FechaRegistro   DATETIME      NOT NULL DEFAULT GETDATE(),
    RegistradoPor   NVARCHAR(50)  NULL,
    ModificadoPor   NVARCHAR(50)  NULL,
    FechaModificado DATETIME      NOT NULL DEFAULT GETDATE()
);

-- Tabla DatosAcademicos
CREATE TABLE rrhh.DatosAcademicos (
    Id              INT IDENTITY(1,1) PRIMARY KEY,
    IdDatosEmpleado INT           NOT NULL REFERENCES rrhh.DatosEmpleados(Id),
    Titulo          NVARCHAR(100) NOT NULL,
    Institucion     NVARCHAR(100) NULL,
    Fecha           DATE          NOT NULL,
    Anexo           NVARCHAR(MAX) NULL,
    FechaRegistro   DATETIME      NOT NULL DEFAULT GETDATE(),
    RegistradoPor   NVARCHAR(50)  NULL,
    ModificadoPor   NVARCHAR(50)  NULL,
    FechaModificado DATETIME      NOT NULL DEFAULT GETDATE()
);
```

## Estructura de archivos

```
app.py
requirements.txt
templates/
  base.html        ← Layout compartido, estilos, navbar
  login.html       ← Tab 1: Login con cédula y ctabanco
  menu.html        ← Tab 2: Menú con sección del empleado
  formulario.html  ← Tab 3: Formulario SCRUD completo
```

## Notas de seguridad

- Cambiar `app.secret_key` a un valor fijo y seguro en producción.
- Considerar usar variables de entorno para las credenciales de BD.
- Habilitar HTTPS en producción.
