-- Script SQL para configurar la autenticación en Supabase
-- Ejecuta este script en el editor SQL de tu proyecto Supabase

-- 1. Agregar columna user_id a la tabla students (si no existe)
ALTER TABLE students 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- 2. Crear índice para mejorar el rendimiento de búsquedas por user_id
CREATE INDEX IF NOT EXISTS students_user_id_idx ON students(user_id);

-- 3. Habilitar Row Level Security (RLS) en la tabla students
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- 4. Crear políticas de seguridad para la tabla students

-- Política: Los usuarios pueden ver solo sus propios datos
DROP POLICY IF EXISTS "Users can view own data" ON students;
CREATE POLICY "Users can view own data" ON students
FOR SELECT USING (auth.uid() = user_id);

-- Política: Los usuarios pueden insertar sus propios datos
DROP POLICY IF EXISTS "Users can insert own data" ON students;
CREATE POLICY "Users can insert own data" ON students
FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Política: Los usuarios pueden actualizar sus propios datos
DROP POLICY IF EXISTS "Users can update own data" ON students;
CREATE POLICY "Users can update own data" ON students
FOR UPDATE USING (auth.uid() = user_id);

-- Política: Los usuarios pueden eliminar sus propios datos
DROP POLICY IF EXISTS "Users can delete own data" ON students;
CREATE POLICY "Users can delete own data" ON students
FOR DELETE USING (auth.uid() = user_id);

-- 5. Configurar la tabla matches (si existe)
-- Agregar user_id si la tabla ya existe
ALTER TABLE matches 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Crear índice
CREATE INDEX IF NOT EXISTS matches_user_id_idx ON matches(user_id);

-- Habilitar RLS
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

-- Políticas para matches
DROP POLICY IF EXISTS "Users can view own matches" ON matches;
CREATE POLICY "Users can view own matches" ON matches
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM students 
        WHERE students.id = matches.student_id 
        AND students.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can insert own matches" ON matches;
CREATE POLICY "Users can insert own matches" ON matches
FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM students 
        WHERE students.id = matches.student_id 
        AND students.user_id = auth.uid()
    )
);

-- 6. Opcional: Crear una función para obtener el perfil del usuario actual
CREATE OR REPLACE FUNCTION get_current_user_profile()
RETURNS TABLE (
    id UUID,
    name TEXT,
    profile_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE SQL
SECURITY DEFINER
AS $$
    SELECT id, name, profile_data, created_at
    FROM students
    WHERE user_id = auth.uid()
    ORDER BY created_at DESC
    LIMIT 1;
$$;

-- 7. Opcional: Crear vista para ver estadísticas del usuario
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    s.user_id,
    s.name,
    COUNT(m.id) as total_matches,
    MAX(m.created_at) as last_match_date
FROM students s
LEFT JOIN matches m ON s.id = m.student_id
GROUP BY s.user_id, s.name;

-- Nota: Después de ejecutar este script:
-- 1. Verifica que las tablas tengan la columna user_id
-- 2. Asegúrate de que RLS esté habilitado
-- 3. Prueba el registro y login en tu aplicación
-- 4. Los datos existentes sin user_id no serán accesibles hasta que se les asigne uno
