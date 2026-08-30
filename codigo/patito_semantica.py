# ============================================================
#  Compilador Patito — Directorio de Funciones y Tabla de Variables
#  Etapa 2: Análisis Semántico
# ============================================================

# ── Tipos válidos del lenguaje ───────────────────────────────
TIPOS_VALIDOS    = {"INT", "FLOAT", "BOOL", "VOID", "ERROR"}
CATEGORIAS_VALIDAS = {"VAR", "PARAM"}

# ── Cubo Semántico ───────────────────────────────────────────
CUBO_SEMANTICO = {
    ("INT",   "INT"):   {"+": "INT",   "-": "INT",   "*": "INT",   "/": "FLOAT",
                         ">": "BOOL",  "<": "BOOL",  "!=": "BOOL", "==": "BOOL",
                         ">=": "BOOL", "<=": "BOOL"},
    ("INT",   "FLOAT"): {"+": "FLOAT", "-": "FLOAT", "*": "FLOAT", "/": "FLOAT",
                         ">": "BOOL",  "<": "BOOL",  "!=": "BOOL", "==": "BOOL",
                         ">=": "BOOL", "<=": "BOOL"},
    ("FLOAT", "INT"):   {"+": "FLOAT", "-": "FLOAT", "*": "FLOAT", "/": "FLOAT",
                         ">": "BOOL",  "<": "BOOL",  "!=": "BOOL", "==": "BOOL",
                         ">=": "BOOL", "<=": "BOOL"},
    ("FLOAT", "FLOAT"): {"+": "FLOAT", "-": "FLOAT", "*": "FLOAT", "/": "FLOAT",
                         ">": "BOOL",  "<": "BOOL",  "!=": "BOOL", "==": "BOOL",
                         ">=": "BOOL", "<=": "BOOL"},
}



def consultar_cubo(tipo_izq: str, tipo_der: str, operador: str) -> str:
    """
    Consulta el cubo semántico.
    Retorna el tipo resultado o 'ERROR' si la operación no es válida.
    """
    clave = (tipo_izq, tipo_der)
    if clave in CUBO_SEMANTICO and operador in CUBO_SEMANTICO[clave]:
        return CUBO_SEMANTICO[clave][operador]
    return "x"


# ============================================================
#  Error semántico
# ============================================================

class SemanticError(Exception):
    """Excepción para errores semánticos del compilador."""
    def __init__(self, mensaje: str):
        super().__init__(f"[Error Semántico] {mensaje}")


class MemoriaVirtual:
    """
    Asigna direcciones virtuales para variables, parámetros,
    temporales y constantes según segmentos de memoria.
    """

    BASES = {
        ("global", "INT"):   1000,
        ("global", "FLOAT"): 1100,
        ("global", "BOOL"):  1200,
        ("local", "INT"):    2000,
        ("local", "FLOAT"):  2100,
        ("local", "BOOL"):   2200,
        ("param", "INT"):    3000,
        ("param", "FLOAT"):  3100,
        ("param", "BOOL"):   3200,
        ("temp", "INT"):     4000,
        ("temp", "FLOAT"):   4100,
        ("temp", "BOOL"):    4200,
        ("const", "INT"):    5000,
        ("const", "FLOAT"):  5100,
        ("const", "BOOL"):   5200,
        ("const", "STRING"): 5300,
    }

    def __init__(self):
        self._contadores = dict(self.BASES)
        self._constantes: dict[tuple[str, str], dict] = {}

    def asignar_direccion(self, segmento: str, tipo: str) -> int:
        clave = (segmento, tipo)
        if clave not in self._contadores:
            raise SemanticError(
                f"Segmento o tipo inválido en memoria virtual: {segmento}, {tipo}"
            )
        direccion = self._contadores[clave]
        self._contadores[clave] += 1
        return direccion

    def asignar_constante(self, valor: str, tipo: str) -> int:
        clave = (valor, tipo)
        if clave in self._constantes:
            return self._constantes[clave]["direccion"]
        direccion = self.asignar_direccion("const", tipo)
        self._constantes[clave] = {
            "valor": valor,
            "tipo": tipo,
            "direccion": direccion,
        }
        return direccion

    def get_constantes_valores(self) -> dict:
        """Retorna {dirección: valor_python} para todas las constantes."""
        import ast
        resultado = {}
        for (valor_str, tipo), info in self._constantes.items():
            addr = info["direccion"]
            if tipo == "INT":
                resultado[addr] = int(valor_str)
            elif tipo == "FLOAT":
                resultado[addr] = float(valor_str)
            elif tipo == "STRING":
                try:
                    resultado[addr] = ast.literal_eval(valor_str)
                except Exception:
                    resultado[addr] = valor_str.strip('"')
            elif tipo == "BOOL":
                resultado[addr] = valor_str.lower() == "true"
            else:
                resultado[addr] = valor_str
        return resultado


# ============================================================
#  Tabla de Variables
#  Columnas: Nombre | Categoria | Tipo | Scope
# ============================================================

class TablaVariables:
    """
    Tabla de Variables de un scope (función o programa principal).

    Estructura interna:
        dict {
            nombre -> {
                categoria : "VAR" | "PARAM",
                tipo      : "INT" | "FLOAT",
                scope     : "global" | nombre_funcion
            }
        }
    """

    def __init__(self, nombre_scope: str):
        self.scope = nombre_scope
        self._tabla: dict[str, dict] = {}

    # ── Verificar existencia ────────────────────────────
    def existe(self, nombre: str) -> bool:
        """Retorna True si la variable ya fue declarada en este scope."""
        return nombre in self._tabla

    # ── Insertar variable o parámetro ───────────────────
    def insertar(self, nombre: str, categoria: str, tipo: str, direccion: int) -> None:
        """
        Inserta una variable o parámetro en la tabla.

        Parámetros:
            nombre    : identificador de la variable
            categoria : 'VAR' o 'PARAM'
            tipo      : 'INT' o 'FLOAT'
            direccion : dirección virtual asignada

        Lanza SemanticError si:
            - La variable ya existe (doblemente declarada)
            - El tipo no es válido
            - La categoría no es válida
        """
        if self.existe(nombre):
            raise SemanticError(
                f"Variable doblemente declarada: '{nombre}' "
                f"en scope '{self.scope}'"
            )
        if tipo not in TIPOS_VALIDOS:
            raise SemanticError(
                f"Tipo inválido: '{tipo}'"
            )
        if categoria not in CATEGORIAS_VALIDAS:
            raise SemanticError(
                f"Categoría inválida: '{categoria}'. "
                f"Debe ser 'VAR' o 'PARAM'"
            )
        self._tabla[nombre] = {
            "categoria": categoria,
            "tipo":      tipo,
            "scope":     self.scope,
            "direccion": direccion,
        }

    # ── Buscar variable (P7, P9) ─────────────────────────────
    def buscar(self, nombre: str) -> dict | None:
        """Retorna el registro completo de la variable o None si no existe."""
        return self._tabla.get(nombre, None)

    def obtener_tipo(self, nombre: str) -> str | None:
        """Retorna el tipo de una variable o None si no existe."""
        registro = self.buscar(nombre)
        return registro["tipo"] if registro else None

    def __repr__(self) -> str:
        encabezado = (
            f"  {'Nombre':<15} {'Categoria':<10} {'Tipo':<8} {'Scope'}"
        )
        separador = "  " + "-" * 45
        filas = "\n".join(
            f"  {nombre:<15} {reg['categoria']:<10} {reg['tipo']:<8} {reg['scope']}"
            for nombre, reg in self._tabla.items()
        )
        return (
            f"TablaVariables(scope='{self.scope}'):\n"
            f"{encabezado}\n"
            f"{separador}\n"
            f"{filas if filas else '  (vacía)'}"
        )


# ============================================================
#  Directorio de Funciones
#  Columnas: Nombre | Tipo retorno | Tabla de Variables
# ============================================================

class DirectorioFunciones:
    """
    Directorio de Funciones del programa.

    Estructura interna:
        dict {
            nombre_func -> {
                tipo_retorno : "VOID | INT | FLOAT ",
                tabla_vars   : TablaVariables
            }
        }
    """

    def __init__(self):
        self._directorio: dict[str, dict] = {}
        self._scope_actual: str | None    = None
        self._memoria = MemoriaVirtual()

    # ── insertar función ─────────────────────────────
    def insertar_funcion(self, nombre: str, tipo_retorno: str = "VOID") -> None:
        """
        Crea una nueva entrada en el directorio.

        Lanza SemanticError si la función ya fue declarada.
        """
        if self.existe_funcion(nombre):
            raise SemanticError(
                f"Función doblemente declarada: '{nombre}'"
            )
        self._directorio[nombre] = {
            "tipo_retorno": tipo_retorno,
            "tabla_vars":   TablaVariables(nombre),
            "returnes":     [],
            "params":       [],
        }
        self._scope_actual = nombre

    # ── abrir scope ──────────────────────────────────────
    def abrir_scope(self, nombre: str) -> None:
        """Establece el scope actual al entrar a una función."""
        if not self.existe_funcion(nombre):
            raise SemanticError(
                f"Función '{nombre}' no encontrada al abrir scope."
            )
        self._scope_actual = nombre

    # ──    cerrar scope ─────────────────────────────────────
    def cerrar_scope(self) -> None:
        """Cierra el scope actual y regresa al scope global."""
        self._scope_actual = self._nombre_global()

    def _nombre_global(self) -> str | None:
        """Retorna el nombre del programa principal (primer scope insertado)."""
        if self._directorio:
            return next(iter(self._directorio))
        return None

    # ── Verificar existencia ─────────────────────────────────
    def existe_funcion(self, nombre: str) -> bool:
        """Retorna True si la función ya fue declarada."""
        return nombre in self._directorio

    # ── buscar función ──────────────────────────────────
    def buscar_funcion(self, nombre: str) -> dict | None:
        """Retorna el registro de la función o None si no existe."""
        return self._directorio.get(nombre, None)

    # ── Tabla de variables del scope actual ──────────────────
    def _tabla_actual(self) -> TablaVariables:
        if self._scope_actual is None:
            raise SemanticError("No hay scope activo.")
        return self._directorio[self._scope_actual]["tabla_vars"]

    def _tabla_global(self) -> TablaVariables:
        nombre_global = self._nombre_global()
        if nombre_global is None:
            raise SemanticError("No hay scope global definido.")
        return self._directorio[nombre_global]["tabla_vars"]

    # ── P2, P3: insertar variable ────────────────────────────
    def insertar_variable(
        self, nombre: str, categoria: str, tipo: str
    ) -> None:
        """
        Inserta una variable o parámetro en la tabla del scope actual.

        Parámetros:
            nombre    : identificador
            categoria : 'VAR' o 'PARAM'
            tipo      : 'INT' o 'FLOAT'
        """
        direccion = self._asignar_direccion_variable(categoria, tipo)
        self._tabla_actual().insertar(nombre, categoria, tipo, direccion)
        if categoria == "PARAM":
            self._directorio[self._scope_actual]["params"].append(tipo)

    def _asignar_direccion_variable(self, categoria: str, tipo: str) -> int:
        nombre_global = self._nombre_global()
        if nombre_global is None:
            raise SemanticError("No hay scope global definido para asignar direcciones.")

        if categoria == "PARAM":
            segmento = "param"
        elif categoria == "VAR":
            segmento = (
                "global" if self._scope_actual == nombre_global else "local"
            )
        else:
            raise SemanticError(
                f"Categoría inválida al asignar dirección: '{categoria}'"
            )
        return self._memoria.asignar_direccion(segmento, tipo)

    def asignar_nueva_temporal(self, tipo: str) -> int:
        return self._memoria.asignar_direccion("temp", tipo)

    def asignar_constante(self, valor: str, tipo: str) -> int:
        return self._memoria.asignar_constante(valor, tipo)

    def registrar_return(self, tipo: str | None) -> None:
        if self._scope_actual is None:
            raise SemanticError("No hay scope activo al registrar RETURN.")
        funcion = self._directorio[self._scope_actual]
        funcion["returnes"].append(tipo)

    def verificar_returnes(self, nombre: str | None = None) -> None:
        if nombre is None:
            nombre = self._scope_actual
        if nombre is None:
            raise SemanticError("No hay scope definido para verificar RETURN.")

        funcion = self.buscar_funcion(nombre)
        if funcion is None:
            raise SemanticError(f"Función '{nombre}' no encontrada para verificar RETURN.")

        tipo_retorno = funcion["tipo_retorno"]
        returnes = funcion.get("returnes", [])
        if not returnes:
            if tipo_retorno != "VOID":
                raise SemanticError(
                    f"Función '{nombre}' debe tener un RETURN de tipo '{tipo_retorno}'."
                )
            else:
                return

        if tipo_retorno == "VOID":
            raise SemanticError(
                f"Función '{nombre}' es VOID y no puede contener RETURN."
            )

        for tipo in returnes:
            if tipo is None:
                raise SemanticError(
                    f"Return en función '{nombre}' debe devolver un valor de tipo '{tipo_retorno}'."
                )
            if tipo != tipo_retorno:
                raise SemanticError(
                    f"Return en función '{nombre}' devuelve '{tipo}', "
                    f"se esperaba '{tipo_retorno}'."
                )

    # ── Soporte para la Máquina Virtual ─────────────────────────

    def registrar_inicio_cuad(self, nombre: str, inicio: int) -> None:
        """Registra el índice del primer cuádruplo de la función."""
        if nombre in self._directorio:
            self._directorio[nombre]["inicio_cuad"] = inicio

    def get_inicio_cuad(self, nombre: str) -> int:
        """Retorna el índice del primer cuádruplo de la función."""
        func = self._directorio.get(nombre)
        if func is None:
            raise RuntimeError(f"Función no encontrada: '{nombre}'")
        return func.get("inicio_cuad", 0)

    def get_params_dir(self, nombre: str) -> list:
        """Retorna las direcciones de los parámetros en orden de declaración."""
        func = self._directorio.get(nombre)
        if func is None:
            raise RuntimeError(f"Función no encontrada: '{nombre}'")
        tabla = func["tabla_vars"]._tabla
        return [reg["direccion"] for reg in tabla.values()
                if reg["categoria"] == "PARAM"]

    def verificar_llamada(self, nombre: str, tipos_args: list) -> None:
        funcion = self.buscar_funcion(nombre)
        if funcion is None:
            raise SemanticError(f"Función no declarada: '{nombre}'")
        params = funcion["params"]
        if len(tipos_args) != len(params):
            raise SemanticError(
                f"Llamada a '{nombre}': se esperaban {len(params)} argumento(s), "
                f"se recibieron {len(tipos_args)}"
            )
        for i, (esperado, recibido) in enumerate(zip(params, tipos_args)):
            if esperado != recibido:
                raise SemanticError(
                    f"Llamada a '{nombre}': argumento {i+1} es '{recibido}', "
                    f"se esperaba '{esperado}'"
                )

    def obtener_registro_variable(self, nombre: str) -> dict:
        registro = self.buscar_variable(nombre)
        if registro is None:
            raise SemanticError(
                f"Variable no declarada: '{nombre}' "
                f"en scope '{self._scope_actual}'"
            )
        return registro

    # ── buscar variable en scope local o global ──────
    def buscar_variable(self, nombre: str) -> dict | None:
        """
        Busca una variable primero en el scope local,
        luego en el scope global.
        Retorna el registro o None si no existe en ninguno.
        """
        registro = self._tabla_actual().buscar(nombre)
        if registro:
            return registro
        nombre_global = self._nombre_global()
        if nombre_global and self._scope_actual != nombre_global:
            registro = self._tabla_global().buscar(nombre)
        return registro

    def obtener_tipo_variable(self, nombre: str) -> str:
        """
        Retorna el tipo de una variable buscando en scope local y global.
        Lanza SemanticError si no existe.
        """
        registro = self.buscar_variable(nombre)
        if registro is None:
            raise SemanticError(
                f"Variable no declarada: '{nombre}' "
                f"en scope '{self._scope_actual}'"
            )
        return registro["tipo"]

    def __repr__(self) -> str:
        separador = "=" * 55
        resultado = f"{separador}\nDirectorio de Funciones\n{separador}"
        encabezado = f"\n  {'Nombre':<20} {'Tipo retorno':<15} {'Tabla de Variables'}"
        resultado += encabezado
        resultado += f"\n  {'-'*50}"
        for nombre, reg in self._directorio.items():
            resultado += (
                f"\n  {nombre:<20} {reg['tipo_retorno']:<15} "
                f"-> TVar_{nombre}"
            )
        resultado += f"\n\n{separador}\nTablas de Variables\n{separador}"
        for nombre, reg in self._directorio.items():
            resultado += f"\n\n{reg['tabla_vars']}"
        return resultado
