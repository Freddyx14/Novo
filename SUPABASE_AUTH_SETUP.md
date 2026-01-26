# Configuración de Autenticación con Supabase

## Pasos para Configurar Supabase Auth

### 1. Crear un Proyecto en Supabase

1. Ve a [https://supabase.com](https://supabase.com) y crea una cuenta
2. Crea un nuevo proyecto
3. Guarda la URL del proyecto y la clave anónima (anon key)

### 2. Configurar Variables de Entorno

Copia el archivo `.env.example` a `.env` y completa las variables:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de Supabase:

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_clave_anon_aqui
SECRET_KEY=genera_una_clave_secreta_aleatoria
```

### 3. Habilitar Autenticación por Email en Supabase

1. Ve a tu proyecto en Supabase
2. En el panel lateral, selecciona **Authentication** → **Providers**
3. Asegúrate de que **Email** esté habilitado
4. Configura las opciones de confirmación de email según prefieras:
   - **Enable email confirmations**: Activa esto si quieres que los usuarios confirmen su email
   - **Disable email confirmations**: Para desarrollo, puedes desactivar esto

### 4. Configurar Row Level Security (RLS) - Opcional pero Recomendado

Si quieres que los datos de los usuarios estén protegidos:

1. Ve a **Database** → **Tables**
2. Para cada tabla que quieras proteger (students, matches, etc.), habilita RLS
3. Crea políticas de seguridad. Ejemplo para la tabla `students`:

```sql
-- Permitir que los usuarios solo vean sus propios datos
CREATE POLICY "Users can view own data" ON students
FOR SELECT USING (auth.uid() = user_id);

-- Permitir que los usuarios inserten sus propios datos
CREATE POLICY "Users can insert own data" ON students
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Permitir que los usuarios actualicen sus propios datos
CREATE POLICY "Users can update own data" ON students
FOR UPDATE USING (auth.uid() = user_id);
```

### 5. Estructura de la Base de Datos

Asegúrate de que tus tablas tengan una columna `user_id` para vincular los datos con el usuario autenticado:

```sql
-- Ejemplo: Agregar columna user_id a la tabla students si no existe
ALTER TABLE students ADD COLUMN user_id UUID REFERENCES auth.users(id);
```

## Uso de la Aplicación

### Registro de Usuario

1. Ve a `/register`
2. Completa el formulario con:
   - Nombre completo
   - Email
   - Contraseña (mínimo 6 caracteres)
3. Si la confirmación de email está habilitada, revisa tu correo

### Inicio de Sesión

1. Ve a `/login`
2. Ingresa tu email y contraseña
3. Serás redirigido a la página de perfil

### Rutas Protegidas

Las siguientes rutas requieren autenticación:
- `/profile` - Subir CV y audio
- `/results` - Ver análisis de perfil
- `/dashboard/<student_id>` - Ver oportunidades

Si intentas acceder sin estar autenticado, serás redirigido a `/login`

## Flujo de la Aplicación

1. **Registro** → Crea una cuenta nueva
2. **Login** → Inicia sesión
3. **Profile** → Sube tu CV y audio (opcional)
4. **Results** → Revisa el análisis de tu perfil
5. **Dashboard** → Explora oportunidades personalizadas
6. **Logout** → Cierra sesión (botón en la barra de navegación)

## Seguridad

- Las contraseñas se almacenan de forma segura con hash en Supabase
- Los tokens de sesión se refrescan automáticamente
- La autenticación usa JWT (JSON Web Tokens)
- Todas las rutas principales están protegidas con el decorador `@login_required`

## Troubleshooting

### Error: "Invalid login credentials"
- Verifica que el email y contraseña sean correctos
- Si usas confirmación de email, asegúrate de haber confirmado tu cuenta

### Error: "SUPABASE_URL or SUPABASE_KEY not set"
- Asegúrate de tener el archivo `.env` configurado correctamente
- Verifica que las variables de entorno estén cargadas

### Los usuarios no pueden registrarse
- Verifica que la autenticación por email esté habilitada en Supabase
- Revisa los logs en el dashboard de Supabase

## Desarrollo Adicional

Si quieres agregar más funcionalidades:

- **OAuth (Google, GitHub, etc.)**: Configura en Supabase → Authentication → Providers
- **Reset de contraseña**: Implementa usando `supabase.auth.reset_password_for_email()`
- **Actualizar perfil**: Usa `supabase.auth.update()` para cambiar email o contraseña
- **Sesiones persistentes**: Ya implementado con Flask sessions
